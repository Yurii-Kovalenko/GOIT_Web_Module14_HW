from typing import List

from sqlalchemy import func, extract, and_, or_

from sqlalchemy.orm import Session

from datetime import date, timedelta

from src.database.models import Contact, User
from src.schemas import ContactModel, ContactUpdate


async def get_contacts(
    skip: int,
    limit: int,
    first_name: str,
    last_name: str,
    email: str,
    birthdays: int,
    user: User,
    db: Session,
) -> List[Contact]:
    """
    Retrieves a list of contacts for a specific user with specified pagination parameters or
    parameters for searching (by first name or last name, or email, or birthdays).

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
    :param user: The user to retrieve contacts for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: A list of contacts.
    :rtype: List[Contact]
    """
    if len(f"{first_name}{last_name}{email}") == 0 and birthdays == 0:
        return (
            db.query(Contact)
            .filter(Contact.user_id == user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    elif len(first_name) > 0:
        return (
            db.query(Contact)
            .filter(
                and_(
                    Contact.first_name.startswith(first_name),
                    Contact.user_id == user.id,
                )
            )
            .all()
        )
    elif len(last_name) > 0:
        return (
            db.query(Contact)
            .filter(
                and_(
                    Contact.last_name.startswith(last_name), Contact.user_id == user.id
                )
            )
            .all()
        )
    elif len(email) > 0:
        return (
            db.query(Contact)
            .filter(and_(Contact.email.startswith(email), Contact.user_id == user.id))
            .all()
        )
    else:
        date_start = date.today()
        year_start = date_start.year
        date_finish = date.today() + timedelta(days=birthdays)
        year_finish = date_finish.year
        return (
            db.query(Contact)
            .filter(
                and_(
                    or_(
                        and_(
                            func.date(
                                func.concat(
                                    year_start,
                                    "-",
                                    extract("month", Contact.date_of_birth),
                                    "-",
                                    extract("day", Contact.date_of_birth),
                                )
                            )
                            >= date_start,
                            func.date(
                                func.concat(
                                    year_start,
                                    "-",
                                    extract("month", Contact.date_of_birth),
                                    "-",
                                    extract("day", Contact.date_of_birth),
                                )
                            )
                            <= date_finish,
                        ),
                        and_(
                            func.date(
                                func.concat(
                                    year_finish,
                                    "-",
                                    extract("month", Contact.date_of_birth),
                                    "-",
                                    extract("day", Contact.date_of_birth),
                                )
                            )
                            >= date_start,
                            func.date(
                                func.concat(
                                    year_finish,
                                    "-",
                                    extract("month", Contact.date_of_birth),
                                    "-",
                                    extract("day", Contact.date_of_birth),
                                )
                            )
                            <= date_finish,
                        ),
                    ),
                    Contact.user_id == user.id,
                )
            )
            .all()
        )


async def get_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    """
    Retrieves a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve.
    :type contact_id: int
    :param user: The user to retrieve the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Contact | None
    """
    return (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.user_id == user.id))
        .first()
    )


async def create_contact(body: ContactModel, user: User, db: Session) -> Contact:
    """
    Creates a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: ContactModel
    :param user: The user to create the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The newly created contact.
    :rtype: Contact
    """
    contact = Contact(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        phone=body.phone,
        date_of_birth=body.date_of_birth,
        user=user,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, user: User, db: Session) -> Contact | None:
    """
    Removes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to remove.
    :type contact_id: int
    :param user: The user to remove the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The removed contact, or None if it does not exist.
    :rtype: Contact | None
    """
    contact = (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.user_id == user.id))
        .first()
    )
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def update_contact(
    contact_id: int, body: ContactModel, user: User, db: Session
) -> Contact | None:
    """
    Updates a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated data for the contact.
    :type body: ContactModel
    :param user: The user to update the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact, or None if it does not exist.
    :rtype: Contact | None
    """
    contact = (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.user_id == user.id))
        .first()
    )
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.date_of_birth = body.date_of_birth
        db.commit()
    return contact


async def update_date_of_birth_contact(
    contact_id: int, body: ContactUpdate, user: User, db: Session
) -> Contact | None:
    """
    Updates the date of birth of a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update.
    :type contact_id: int
    :param body: The updated date of birth for the contact.
    :type body: ContactUpdate
    :param user: The user to update the contact for.
    :type user: User
    :param db: The database session.
    :type db: Session
    :return: The updated contact, or None if it does not exist.
    :rtype: Contact | None
    """
    contact = (
        db.query(Contact)
        .filter(and_(Contact.id == contact_id, Contact.user_id == user.id))
        .first()
    )
    if contact:
        contact.date_of_birth = body.date_of_birth
        db.commit()
    return contact
