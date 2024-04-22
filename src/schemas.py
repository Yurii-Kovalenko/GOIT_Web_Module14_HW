"""
Models for validating incoming data through pydantic
"""
from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, EmailStr, PastDate


class ContactModel(BaseModel):
    """
    Contact model to be added to the database by the user
    """
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    date_of_birth: PastDate
    email: Optional[EmailStr] = Field(None)
    phone: Optional[str] = Field(None, max_length=20)


class ContactUpdate(BaseModel):
    """
    Contact model for changing date of birth
    """
    date_of_birth: PastDate


class ContactResponse(ContactModel):
    """
    Contact model for the database and for responding to a request
    """
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserModel(BaseModel):
    """
    User model to be added to the database by the user
    """
    username: str = Field(min_length=5, max_length=50)
    email: EmailStr = Field(min_length=10, max_length=250)
    password: str = Field(min_length=8, max_length=100)


class UserDb(BaseModel):
    """
    User model for the database
    """
    id: int
    username: str
    email: EmailStr
    avatar: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """
    User model for responding to the request when creating the new user
    """
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    """
    Token user model
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """
    User model for the email
    """
    email: EmailStr


class RequestPassword(BaseModel):
    """
    User model for password change
    """
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
