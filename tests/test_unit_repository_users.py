"""
Для виконання потрібна копія файлу .env в папці tests
"""

import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session
from redis import Redis

from src.database.models import User
from src.schemas import UserModel, UserDb, UserResponse, TokenModel, RequestEmail, RequestPassword
from src.repository.users import (
    get_user_by_email_from_db,
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_password,
    update_avatar,
    redis_db
)


class TestNotes(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(username="test_user", email="test_user@google.com", password="12345678")
        self.redis_db = MagicMock(spec=Redis)

    async def test_get_user_by_email_from_db_found(self):
        user = self.user
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email_from_db(email=self.user.email, db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_from_db_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email_from_db(email=self.user.email, db=self.session)
        self.assertIsNone(result)

    async def test_get_user_by_email_found(self):
        redis_db.get = MagicMock(return_value=None)
        redis_db.set = MagicMock(return_value=None)
        user = self.user
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email=self.user.email, db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        redis_db.get = MagicMock(return_value=None)
        redis_db.set = MagicMock(return_value=None)
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email=self.user.email, db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        redis_db.get = MagicMock(return_value=None)
        body = UserModel(username=self.user.username, email=self.user.email, password=self.user.password)
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertTrue(hasattr(result, "id"))
        self.session.commit.assert_called_once()

    async def test_update_token(self):
        redis_db.get = MagicMock(return_value=None)
        user = self.user
        token = "test_token"
        self.session.query().filter().first.return_value = user
        await update_token(cache_user=user, token=token, db=self.session)
        self.assertEqual(user.refresh_token, token)
        self.session.commit.assert_called_once()

    async def test_confirmed_email(self):
        redis_db.get = MagicMock(return_value=None)
        user = self.user
        self.session.query().filter().first.return_value = user
        await confirmed_email(email=user.email, db=self.session)
        self.assertTrue(user.confirmed)
        self.session.commit.assert_called_once()

    async def test_update_password(self):
        redis_db.get = MagicMock(return_value=None)
        user = self.user
        new_password = "test_password"
        self.session.query().filter().first.return_value = user
        await update_password(cache_user=user, password=new_password, db=self.session)
        self.assertEqual(user.password, new_password)
        self.session.commit.assert_called_once()

    async def test_update_avatar(self):
        redis_db.get = MagicMock(return_value=None)
        user = self.user
        new_url = "test_url"
        self.session.query().filter().first.return_value = user
        await update_avatar(email=user.email, url=new_url, db=self.session)
        self.assertEqual(user.avatar, new_url)
        self.session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()