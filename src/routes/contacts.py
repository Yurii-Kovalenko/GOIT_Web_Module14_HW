from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactModel, ContactUpdate, ContactResponse
from src.repository import contacts as repository_contacts
from src.services.auth import auth_service
from src.database.models import User, Contact

router = APIRouter(prefix="/contacts", tags=["contacts"])

contact_not_found = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
)


@router.get("/", response_model=List[ContactResponse], description='No more than 5 requests per 30 seconds',
            dependencies=[Depends(RateLimiter(times=5, seconds=30))])
async def read_contacts(
        skip: int = 0,
        limit: int = 20,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        birthdays: int = 0,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
) -> list[Contact]:
    """
    Provides the server's response to request to the list of contacts for a specific user
    with specified pagination parameters or parameters for searching (by first name or
    last name, or email, or birthdays).

    :param skip: The number of contacts to skip.
    :type skip: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param first_name: The string with which the contact first name begins (search by first name).
    :type first_name: str
    :param last_name: The string with which the contact last name begins (search by last name).
    :type last_name: str
    :param email: The string with which the contact email begins (search by email).
    :type email: str
    :param birthdays: The number of days in which the contact's birthday will be next (search by birthday).
    :type birthdays: int
    :param current_user: The user to retrieve contacts for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contact]
    """
    contacts = await repository_contacts.get_contacts(
        skip, limit, first_name, last_name, email, birthdays, current_user, db
    )
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse, description='No more than 5 requests per 30 seconds',
            dependencies=[Depends(RateLimiter(times=5, seconds=30))])
async def read_contact(
        contact_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
) -> Contact:
    """
    Provides the server's response to request to the single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param current_user: The user to retrieve the contact for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified ID.
    :rtype: Contact
    """
    contact = await repository_contacts.get_contact(contact_id, current_user, db)
    if contact is None:
        raise contact_not_found
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED,
             description='No more than 2 requests per 30 seconds',
             dependencies=[Depends(RateLimiter(times=2, seconds=30))])
async def create_contact(
        body: ContactModel,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
) -> Contact:
    """
    Provides the server's response to request to create a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: ContactModel
    :param current_user: The user to create the contact for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The newly created contact.
    :rtype: Contact
    """
    return await repository_contacts.create_contact(body, current_user, db)


@router.put("/{contact_id}", response_model=ContactResponse, description='No more than 5 requests per 30 seconds',
            dependencies=[Depends(RateLimiter(times=5, seconds=30))])
async def update_contact(
        body: ContactModel,
        contact_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
) -> Contact:
    """
    Provides the server's response to request to update a single contact with the specified ID for a specific user.

    :param body: The updated data for the contact.
    :type body: ContactModel
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param current_user: The user to update the contact for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact.
    :rtype: Contact
    """
    contact = await repository_contacts.update_contact(
        contact_id, body, current_user, db
    )
    if contact is None:
        raise contact_not_found
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse, description='No more than 5 requests per 30 seconds',
              dependencies=[Depends(RateLimiter(times=5, seconds=30))])
async def update_date_of_birth_contact(
        body: ContactUpdate,
        contact_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
) -> Contact:
    """
    Provides the server's response to request to update the date of birth of a single contact
    with the specified ID for a specific user.

    :param body: The updated date of birth for the contact.
    :type body: ContactUpdate
    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param current_user: The user to update the contact for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact.
    :rtype: Contact
    """
    contact = await repository_contacts.update_date_of_birth_contact(
        contact_id, body, current_user, db
    )
    if contact is None:
        raise contact_not_found
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse, description='No more than 5 requests per 30 seconds',
               dependencies=[Depends(RateLimiter(times=5, seconds=30))])
async def remove_contact(
        contact_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db)
) -> Contact:
    """
    Provides the server's response to request to remove a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param current_user: The user to remove the contact for.
    :type current_user: User
    :param db: The database session.
    :type db: Session
    :return: The removed contact.
    :rtype: Contact
    """
    contact = await repository_contacts.remove_contact(contact_id, current_user, db)
    if contact is None:
        raise contact_not_found
    return contact
