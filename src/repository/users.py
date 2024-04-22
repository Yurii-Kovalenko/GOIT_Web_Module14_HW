from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel
from src.conf.config import settings

from redis import Redis
from pickle import dumps, loads

redis_db = Redis(host=settings.redis_host, port=settings.redis_port, db=0)


async def get_user_by_email_from_db(email: str, db: Session) -> User:
    """
    Retrieves a single user with the specified email from the database.

    :param email: The email of the user to retrieve.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: The user with the specified email from the database.
    :rtype: User
    """
    return db.query(User).filter(User.email == email).first()


async def get_user_by_email(email: str, db: Session) -> User:
    """
    Retrieves a single user with the specified email from the caсhe (redis) or from the database.

    :param email: The email of the user to retrieve.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: The user with the specified email from the caсhe (redis) or from the database.
    :rtype: User
    """
    user_dump = redis_db.get(email)
    if user_dump is None:
        user = db.query(User).filter(User.email == email).first()
        redis_db.set(email, dumps(user))
        return user
    return loads(user_dump)


async def create_user(body: UserModel, db: Session) -> User:
    """
    Creates a new user.

    :param body: The data for the user to create.
    :type body: UserModel
    :param db: The database session.
    :type db: Session
    :return: The newly created user.
    :rtype: User
    """
    new_user = User(**body.dict())
    new_user.avatar = ""
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user_dump = redis_db.get(new_user.email)
    if user_dump:
        redis_db.delete(new_user.email)
    return new_user


async def update_token(cache_user: User, token: str | None, db: Session) -> None:
    """
    Updates the refresh token of the user.

    :param cache_user: The user to update the refresh token for.
    :type cache_user: User
    :param token: The updated refresh token for the user.
    :type token: str | None
    :param db: The database session.
    :type db: Session
    :return: The function does not return anything; the user data in the database is modified.
    :rtype: None
    """
    user = await get_user_by_email_from_db(cache_user.email, db)
    user.refresh_token = token
    db.commit()
    user_dump = redis_db.get(user.email)
    if user_dump:
        redis_db.delete(user.email)


async def confirmed_email(email: str, db: Session) -> None:
    """
    Sets a variable indicating that the user has confirmed the email.

    :param email: The email of the user.
    :type email: str
    :param db: The database session.
    :type db: Session
    :return: The function does not return anything; the user data in the database is modified.
    :rtype: None
    """
    user = await get_user_by_email_from_db(email, db)
    user.confirmed = True
    db.commit()
    user_dump = redis_db.get(email)
    if user_dump:
        redis_db.delete(email)


async def update_password(cache_user: User, password: str, db: Session) -> None:
    """
    Updates the password of the user.

    :param cache_user: The user to update the password for.
    :type cache_user: User
    :param password: The updated password for the user.
    :type password: str
    :param db: The database session.
    :type db: Session
    :return: The function does not return anything; the user data in the database is modified.
    :rtype: None
    """
    user = await get_user_by_email_from_db(cache_user.email, db)
    user.password = password
    db.commit()
    user_dump = redis_db.get(user.email)
    if user_dump:
        redis_db.delete(user.email)


async def update_avatar(email, url: str, db: Session) -> User:
    """
    Updates the avatar url of the user.

    :param email: The email of the user.
    :type email: str
    :param url: The updated avatar url for the user.
    :type url: str
    :param db: The database session.
    :type db: Session
    :return: The user with changed avatar url.
    :rtype: User
    """
    user = await get_user_by_email_from_db(email, db)
    user.avatar = url
    db.commit()
    user_dump = redis_db.get(email)
    if user_dump:
        redis_db.delete(email)
    return user
