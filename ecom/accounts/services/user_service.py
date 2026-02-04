from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


@transaction.atomic
def create_user(data: dict) -> User:
    """
    Create a new User instance.

    Uses the User model's `create_user` method to ensure the password
    is hashed and the user is properly created.

    The operation is atomic: if anything fails, the transaction is rolled back.

    Args:
        data (dict): Dictionary of user fields, e.g.,
                     email, password, first_name, last_name, phone_number, role.

    Returns:
        User: The newly created User instance.
    """
    return User.objects.create_user(**data)


@transaction.atomic
def update_user(user: User, data: dict) -> User:
    """
    Update an existing User instance.

    Updates all provided fields in the `data` dictionary and saves the user.

    Args:
        user (User): The User instance to update.
        data (dict): Dictionary of fields to update.

    Returns:
        User: The updated User instance.
    """
    password = data.pop("password", None)
    for field, value in data.items():
        setattr(user, field, value)
    
    if password:
        user.set_password(password)
    
    user.save()
    return user


@transaction.atomic
def delete_user(user: User) -> None:
    """
    Delete an existing User instance.

    The deletion is atomic: either the user is fully deleted or no changes occur
    in case of an error.

    Args:
        user (User): The User instance to delete.

    Returns:
        None
    """
    user.delete()
