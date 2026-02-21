from django.db import transaction
from django.contrib.auth import get_user_model
from accounts.services.email_verification import EmailVerificationService
from core.utils.mail_sender import send_mail_helper

User = get_user_model()


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
    
    with transaction.atomic():
        user = User.objects.create_user(**data)

        transaction.on_commit(
            lambda: send_mail_helper.delay(
                "Welcome",
                f"Hi {user.first_name}!\nYour registration was successful",
                user.email,
            )
        )

        transaction.on_commit(
            lambda: send_mail_helper.delay(
                "Email Verification Link",
                EmailVerificationService.generate_email_token(user.pk),
                user.email,
            )
        )

    return user



@transaction.atomic
def update_user(user, data: dict):
    m2m_fields = []

    for field, value in data.items():

        # ✅ Handle password correctly
        if field == "password":
            if value:
                user.set_password(value)
            continue

        attr = getattr(type(user), field, None)

        # Handle ManyToMany fields
        if hasattr(attr, "field") and attr.field.many_to_many:
            m2m_fields.append((field, value))
        else:
            setattr(user, field, value)

    user.save()

    # Handle M2M separately
    for field, value in m2m_fields:
        getattr(user, field).set(value)

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
