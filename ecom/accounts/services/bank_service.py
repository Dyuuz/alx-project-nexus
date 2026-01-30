from django.db import transaction
from accounts.models import BankAccount


@transaction.atomic
def create_bank_account(vendor, data):
    """
    Create a new BankAccount instance for a given vendor.

    This function ensures that the creation is atomic—either it fully succeeds
    or rolls back in case of an error.

    Args:
        vendor (User): The vendor (user) who owns the bank account.
        data (dict): Dictionary of bank account fields, e.g.,
                     number, name, bank_name, bank_code, subaccount_code.

    Returns:
        BankAccount: The newly created BankAccount instance.
    """
    bank_account = BankAccount.objects.create(vendor=vendor, **data)
    
    # Background task to verify bank account and send a mail when verified
    return bank_account



@transaction.atomic
def update_bank_account(bank_account, data):
    """
    Update an existing BankAccount instance with new data.

    The update is performed atomically to ensure data consistency.

    Args:
        bank_account (BankAccount): The BankAccount instance to update.
        data (dict): Dictionary of fields to update.

    Returns:
        BankAccount: The updated BankAccount instance.
    """
    for field, value in data.items():
        setattr(bank_account, field, value)
    bank_account.save()
    return bank_account


@transaction.atomic
def delete_bank_account(bank_account):
    """
    Delete an existing BankAccount instance.

    This operation is atomic and ensures that deletion fully completes
    or rolls back in case of failure.

    Args:
        bank_account (BankAccount): The BankAccount instance to delete.

    Returns:
        None
    """
    bank_account.delete()
