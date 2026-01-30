from django.db import transaction
from accounts.models import Vendor, CustomUser


@transaction.atomic
def create_vendor(user, data):
    """
    Create a new Vendor instance and assign the user a 'vendor' role.

    This function creates the Vendor linked to the given user, and updates
    the user's role in the CustomUser model to "vendor". The operation is atomic:
    either both the Vendor creation and user role update succeed, or none are applied.

    Args:
        user (CustomUser): The user who will own the vendor account.
        data (dict): Dictionary of vendor fields, e.g., business_name, business_address.

    Returns:
        Vendor: The newly created Vendor instance.
    """
    vendor = Vendor.objects.create(user=user, **data)
    CustomUser.objects.filter(id=user.id).update(role="vendor")
    
    return vendor


@transaction.atomic
def update_vendor(vendor: Vendor, data):
    """
    Update an existing Vendor instance with new data.

    Args:
        vendor (Vendor): The Vendor instance to update.
        data (dict): Dictionary of fields to update.

    Returns:
        Vendor: The updated Vendor instance.
    """
    for field, value in data.items():
        setattr(vendor, field, value)
    vendor.save()
    return vendor


@transaction.atomic
def delete_vendor(vendor: Vendor):
    """
    Delete an existing Vendor instance.

    This operation is atomic and ensures that the vendor is fully deleted or
    no changes occur in case of an error.

    Args:
        vendor (Vendor): The Vendor instance to delete.

    Returns:
        None
    """
    vendor.delete()
