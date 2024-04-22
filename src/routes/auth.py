from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail, RequestPassword
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email, send_email_reset_password


router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request,
                 db: Session = Depends(get_db)):
    """
    Provides the server's response to the user's registration request.

    :param body: New user data.
    :type body: UserModel
    :param background_tasks: Variable for background tasks(to send a letter to the user).
    :type background_tasks: BackgroundTasks
    :param request: User registration request.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Dict with new user information and registration details
    :rtype: dict
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel, status_code=status.HTTP_201_CREATED)
async def login(body: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    """
    Provides the server's response to the user's login request.

    :param body: Login user data.
    :type body: OAuth2PasswordRequestForm
    :param db: The database session.
    :type db: Session
    :return: Dict with user tokens.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = await auth_service.create_access_token(data_payload={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data_payload={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security),
                        db: Session = Depends(get_db)):
    """
    Provides the server's response to the request to update user tokens.

    :param credentials: Login user data.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session.
    :type db: Session
    :return: Dict with new user tokens.
    :rtype: dict
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access_token = await auth_service.create_access_token(data_payload={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data_payload={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Provides the server's response to the email confirmation request.

    :param token: Email confirmation token.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Dict with information about email confirmation.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email', status_code=status.HTTP_201_CREATED)
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Provides the server's response to request to resend letter confirmation email.

    :param body: User email.
    :type body: RequestEmail
    :param background_tasks: Variable for background tasks(to send a letter to the user).
    :type background_tasks: BackgroundTasks
    :param request: User request to resend letter confirmation email.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Dict with information about email confirmation.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        if user.confirmed:
            return {"message": "Your email is already confirmed"}
        else:
            background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.post('/password_reset', status_code=status.HTTP_201_CREATED)
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Provides the server's response to password reset request.

    :param body: User email.
    :type body: RequestEmail
    :param background_tasks: Variable for background tasks(to send a letter to the user).
    :type background_tasks: BackgroundTasks
    :param request: User request to password reset request.
    :type request: Request
    :param db: The database session.
    :type db: Session
    :return: Dict with information about password reset.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        background_tasks.add_task(send_email_reset_password, user.email, user.username, request.base_url)
    return {"message": "Check your email for instruction."}


@router.get('/confirm_password_reset/{token}')
async def confirm_password_reset(token: str, db: Session = Depends(get_db)):
    """
    Provides the server's response to password reset confirmation request.

    :param token: Password reset confirmation token.
    :type token: str
    :param db: The database session.
    :type db: Session
    :return: Dict with information about password reset confirmation.
    :rtype: dict
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirm password reset error")
    return {"email": email, "message": "User confirmed password reset"}


@router.post("/new_password", status_code=status.HTTP_201_CREATED)
async def signup(body: RequestPassword, db: Session = Depends(get_db)):
    """
    Provides the server's response to password reset confirmation request.

    :param body: User email and new user password.
    :type body: RequestPassword
    :param db: The database session.
    :type db: Session
    :return: Dict with information about updating the password.
    :rtype: dict
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email")
    password_hash = auth_service.get_password_hash(body.password)
    await repository_users.update_password(user, password_hash, db)
    return {"message": "Password updated"}
