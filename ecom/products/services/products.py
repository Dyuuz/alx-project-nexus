from django.db import transaction
from products.models import Product
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from collections import defaultdict
from django.db import transaction
from django.db.models import Sum
from django.db.models import F
from core.utils.mail_sender import send_mail_helper
from orders.models import OrderItem
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def create_product(**data):
    """
    Creates a new product and initializes stock and pricing.

    Sets `initial_stock` from the provided stock value and
    applies pricing rules before persisting the product.
    """

    stock = data.get("stock", 0)

    product = Product(
        **data,
        initial_stock=stock,
    )

    _apply_pricing(product)
    product.save()

    return product

@transaction.atomic
def update_product(product_id, **data):
    """
    Updates a product while enforcing stock and pricing rules.

    Stock changes are handled explicitly to keep `initial_stock`,
    alerts, and inventory state consistent.
    """
    data.pop("vendor", None)

    product = Product.objects.select_for_update().get(id=product_id)

    # Handle stock change explicitly
    if "stock" in data:
        new_stock = data.pop("stock")

        if new_stock != product.stock:
            delta = new_stock - product.stock

            # If stock increased → restock → increase initial_stock
            if delta > 0:
                Product.objects.filter(pk=product.pk).update(
                    initial_stock=F("initial_stock") + delta
                )
                product.initial_stock += delta  # keep in-memory sync

            product.update_stock(new_stock)

    # Apply remaining fields
    for key, value in data.items():
        setattr(product, key, value)

    _apply_pricing(product)
    product.reconcile_stock_alerts()
    product.save()

    return product


@transaction.atomic
def delete_product(product):
    """
    Deletes a product instance.
    """
    product.delete()


def _apply_pricing(product):
    """
    Computes and applies the product discount amount
    based on the current pricing configuration.
    """
    if product.discount_percent:
        product.discount_amount = (
            product.original_price * product.discount_percent / 100
        )
    else:
        product.discount_amount = 0


def should_send_critical_stock_alert(self):
    """
    Determines whether a critical stock alert should be sent.

    An alert is triggered when stock falls below the threshold
    and the product has remained inactive beyond the configured window.
    """
    CRITICAL_INACTIVITY_HOURS = settings.CRITICAL_INACTIVITY_HOURS
    if self.stock > self.low_stock_threshold:
        return False

    if self.critical_stock_alert_sent:
        return False

    expiry_time = self.last_activity_at + timedelta(hours=CRITICAL_INACTIVITY_HOURS)
    return timezone.now() >= expiry_time


@transaction.atomic
def send_critical_stock_alerts(self):
    """
    Sends ONE critical stock alert email per vendor,
    containing ALL eligible products.
    """

    products = (
        Product.objects
        .select_related("vendor")
        .filter(
            stock__lte=F("low_stock_threshold"),
            critical_stock_alert_sent=False,
        )
    )

    # Group products by vendor
    vendor_products = defaultdict(list)

    for product in products:
        if product.should_send_critical_stock_alert():
            vendor_products[product.vendor].append(product)

    # Send ONE email per vendor
    for vendor, products in vendor_products.items():
        try:
            # Lock all products for this vendor
            locked_products = (
                Product.objects
                .select_for_update()
                .filter(id__in=[prod.id for prod in products])
            )

            # Re-check after locking 
            eligible_products = [
                prod for prod in locked_products
                if prod.should_send_critical_stock_alert()
            ]

            if not eligible_products:
                continue

            # Send a single email with all products
            send_mail_helper(
                vendor=vendor,
                products=eligible_products,
            )

            # Mark all as alerted
            Product.objects.filter(
                id__in=[prod.id for prod in eligible_products]
            ).update(critical_stock_alert_sent=True)

        except Exception as exc:
            logger.error(
                "Failed to send critical stock alert for vendor %s",
                vendor.id,
                exc_info=True,
            )
            raise self.retry(exc=exc)
        

def reconcile_inventory_and_notify(self):
    """
    Daily inventory audit.
    Detects stock inconsistencies and emails vendors
    a batched report of affected products.
    """

    sold_map = (
        OrderItem.objects
        .filter(order__status="paid")
        .values("product_id")
        .annotate(total_sold=Sum("quantity"))
    )

    sold_by_product = {
        row["product_id"]: row["total_sold"]
        for row in sold_map
    }

    # Group inconsistencies by vendor
    vendor_issues = defaultdict(list)

    for product in Product.objects.select_related("vendor"):
        sold_quantity = sold_by_product.get(product.id, 0)
        expected_stock = product.initial_stock - sold_quantity

        if product.stock != expected_stock:
            vendor_issues[product.vendor].append({
                "product": product,
                "expected": expected_stock,
                "actual": product.stock,
            })

    # Send ONE email per vendor
    for vendor, issues in vendor_issues.items():
        lines = [
            f"- {item['product'].name}: "
            f"expected {item['expected']}, "
            f"actual {item['actual']}"
            for item in issues
        ]
        send_mail_helper(vendor, lines)