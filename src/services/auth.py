from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.conf.config import settings


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    def verify_password(self, plain_password: str, hashed_password:str) -> bool:
        """
        Verifies the password in the usual form and the password in the hashed form.

        :param plain_password: The password in the usual form.
        :type plain_password: str
        :param hashed_password: The password in the hashed form.
        :type hashed_password: str
        :return: True if the verification is successful, otherwise - False.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hashes the password, i.e. returns the password in the hashed form from the password in the usual form.

        :param password: The password in the usual form.
        :type password: str
        :return: The password in the hashed form.
        :rtype: str
        """
        return self.pwd_context.hash(password)

    async def create_access_token(self, data_payload: dict, expires_delta_sec: Optional[float] = None) -> str:
        """
        Retrieves the access token.

        :param data_payload: The data for the access token to create.
        :type data_payload: dict
        :param expires_delta_sec: The time until the token expires in seconds, if not specified, then 15 minutes.
        :type expires_delta_sec: Optional[float] | None
        :return: The access token.
        :rtype: str
        """
        to_encode = data_payload.copy()
        if expires_delta_sec:
            expire = datetime.now() + timedelta(seconds=expires_delta_sec)
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data_payload: dict, expires_delta_sec: Optional[float] = None) -> str:
        """
        Retrieves the refresh token.

        :param data_payload: The data for the refresh token to create.
        :type data_payload: dict
        :param expires_delta_sec: The time until the token expires in seconds, if not specified, then 7 days.
        :type expires_delta_sec: Optional[float] | None
        :return: The refresh token.
        :rtype: str
        """
        to_encode = data_payload.copy()
        if expires_delta_sec:
            expire = datetime.now() + timedelta(seconds=expires_delta_sec)
        else:
            expire = datetime.now() + timedelta(days=7)
        to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str) -> str:
        """
        Retrieves the email of the user using the refresh token.

        :param refresh_token: The refresh token of the user.
        :type refresh_token: str
        :return: The email of the user.
        :rtype: str
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """
        Retrieves the user using the access token.

        :param token:The access token of the user.
        :type token: str
        :param db: The database session.
        :type db: Session
        :return: The user with the specified access token.
        :rtype: User
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception
        return user

    def create_email_token(self, data: dict) -> str:
        """
        Retrieves the token for email verification.

        :param data: The data for the token to create.
        :type data: dict
        :return: The token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=7)
        to_encode.update({"iat": datetime.now(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str) -> str:
        """
        Retrieves the email of the user using the token.

        :param token: The token of the user.
        :type token: str
        :return: The email of the user.
        :rtype: str
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()
