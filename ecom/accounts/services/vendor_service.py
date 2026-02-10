from django.db import transaction
from accounts.models import Vendor, CustomUser
from products.models import Product
from collections import defaultdict
from asgiref.sync import async_to_sync
from core.utils.mail_sender import send_mail_helper
import logging

logger = logging.getLogger(__name__)


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


@transaction.atomic
def send_vendor_low_stock_alerts(self, product_ids):
    """
    Sends one low-stock email per vendor, batching all affected products.
    """
    try:
        products = (
            Product.objects
            .select_related("vendor")
            .filter(
                id__in=product_ids,
                low_stock_alert_sent=False,
            )
        )

        products_by_vendor = defaultdict(list)

        for product in products:
            products_by_vendor[product.vendor].append(product)

        for vendor, vendor_products in products_by_vendor.items():
            if not vendor.email:
                continue

            lines = []
            for product in vendor_products:
                lines.append(
                    f"- {product.name}: {product.stock} left "
                    f"(threshold {product.low_stock_threshold})"
                )

            message = (
                "The following products are running low on stock:\n\n"
                + "\n".join(lines)
                + "\n\nPlease restock to avoid selling out."
            )

            if async_to_sync(send_mail_helper)():
                # Mark all products as alerted
                Product.objects.filter(
                    id__in=[p.id for p in vendor_products]
                ).update(low_stock_alert_sent=True)

    except Exception:
        logger.exception("Failed to send vendor low stock alerts")
        raise
