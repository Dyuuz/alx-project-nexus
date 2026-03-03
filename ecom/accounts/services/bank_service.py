from django.db import transaction
from accounts.models import BankAccount
from core.utils.mail_sender import send_mail_helper
from core.exceptions import ConflictException
from django.db.models import F


@transaction.atomic
def create_bank_account(vendor, data):
    """
    Create a new BankAccount instance for a given vendor.

    This function ensures that the creation is atomic—either it fully succeeds
    or rolls back in case of an error.

    Args:
        vendor (User): The vendor (user) who owns the bank account.
        data (dict): Dictionary of bank account fields, e.g.,
                     number, name, bank_name.

    Returns:
        BankAccount: The newly created BankAccount instance.
    """
    bank_account = BankAccount.objects.create(
        vendor=vendor,
        **data
    )
    
    transaction.on_commit(
        lambda: send_mail_helper.delay(
            "Bank Account Creation Successful",
            f"Hi {vendor.user.first_name}!\nYour bank account has been created successfully.",
            vendor.user.email,
        )
    )

    return bank_account


@transaction.atomic
def update_bank_account(bank_account_id,  data: dict, current_version: int):
    """
    Update an existing BankAccount instance with new data.

    The update is performed atomically to ensure data consistency.

    Args:
        bank_account (BankAccount): The BankAccount instance to update.
        data (dict): Dictionary of fields to update.

    Returns:
        BankAccount: The updated BankAccount instance.
    """
    updated = BankAccount.objects.filter(
        id=bank_account_id,
        version=current_version
    ).update(
        **data,
        version=F('version') + 1
    )

    if updated == 0:
        raise ConflictException()

    updated_instance = BankAccount.objects.get(id=bank_account_id)

    transaction.on_commit(
        lambda: send_mail_helper.delay(
            "Bank Account Update Successful",
            f"Hi {updated_instance.vendor.user.first_name}!\nYour bank account has been updated successfully.",
            updated_instance.vendor.user.email,
        )
    )

    return BankAccount.objects.get(id=bank_account_id)


@transaction.atomic
def delete_bank_account(bank_account_id):
    """
    Delete an existing BankAccount instance.

    This operation is atomic and ensures that deletion fully completes
    or rolls back in case of failure.

    Args:
        bank_account (BankAccount): The BankAccount instance to delete.

    Returns:
        None
    """
    bank_account = BankAccount.objects.get(pk=bank_account_id)
    first_name = bank_account.vendor.user.first_name
    email = bank_account.vendor.user.email
    bank_account.delete()
    
    transaction.on_commit(
        lambda: send_mail_helper.delay(
            "Bank Account Deletion Successful",
            f"Hi {first_name}!\nYour account is deleted successfully",
            email,
        )
    )
