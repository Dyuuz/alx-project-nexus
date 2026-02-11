from decimal import Decimal
from django.db import transaction, IntegrityError
from django.db.models import F
from rest_framework.exceptions import ValidationError
import rest_framework.exceptions as drf_exc
from django.core.exceptions import ObjectDoesNotExist

from cart.models import Cart
from cart.models import CartItem
from cart.models import Checkout
from products.models import Product
from orders.models import Order, OrderItem

from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError
from kombu.exceptions import OperationalError as KombuOperationalError
from orders.models import Order

import logging
logger = logging.getLogger(__name__)


class OrderService:
    """
    Service layer responsible for managing order operations.
    """
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order, reason: str):
        """
        
        """
        if order.status != "awaiting_payment":
            return

        order.cancel(reason=reason)
        return True
    
    @staticmethod
    def create_order_with_cart_recovery(cart):
        """
        Creates an order from a confirmed checkout with automatic cart recovery on failure.

        On validation errors, the cart is reverted to "unpaid" to allow user correction
        before retrying order creation.
        """
        try:
            return OrderService.create_order_from_confirmed_checkout(cart)
            

        except drf_exc.ValidationError as exc:
            try:
                Cart.objects.filter(id=cart.id).exclude(status="unpaid").update(status="unpaid")
                cart.refresh_from_db()
                print(f"Cart {cart.id} reverted to unpaid.")
                
            except IntegrityError:
                print("Recovery skipped due to constraint.")

            raise exc
    
    @staticmethod
    @transaction.atomic
    def create_order_from_confirmed_checkout(cart: Cart) -> Order:
        """
        Create an order from a confirmed checkout.

        Only allows order creation when the cart is in a pending state.
        Snapshots product and pricing data into order items and reduces stock.
        Ensures idempotency by returning an existing order if one already exists.
        """
        from core.tasks import send_vendor_low_stock_alerts_task
        
        if cart.status != "pending":
            raise ValidationError("Checkout must be confirmed before an order can be created.")

        existing_order = Order.objects.filter(cart=cart).first()
        if existing_order:
            return existing_order # idempotent
        
        try:
            checkout: Checkout = cart.checkout
            
        except ObjectDoesNotExist:
            raise ValidationError("Checkout does not exist for this cart.")

        # Lock cart items rows for consistent read
        cart_items = CartItem.objects.select_for_update().filter(cart=cart).select_related("product")
        
        low_stock_product_ids = []

        for item in cart_items:
            product = item.product

            if item.item_quantity > product.stock:
                raise ValidationError(
                    f"Insufficient stock for {product.name}"
                )

            previous_stock = product.stock
            product.stock -= item.item_quantity
            product.save(update_fields=["stock"])

            if (
                previous_stock > product.low_stock_threshold
                and product.stock <= product.low_stock_threshold
                and not product.low_stock_alert_sent
            ):
                low_stock_product_ids.append(product.id)

        if low_stock_product_ids:
            send_vendor_low_stock_alerts_task.delay(low_stock_product_ids)
        
        order = Order.objects.create(
            customer=cart.customer,
            cart=cart,
            status="awaiting_payment",
            shipping_address=checkout.shipping_address,
            billing_address=checkout.billing_address or checkout.shipping_address,
            payment_method=checkout.payment_method,
        )

        # Snapshot each item
        OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product_id=ci.product.id,
            product_name=ci.product.name,
            unit_price=ci.product.original_price,
            discount_percent=int(ci.product.discount_percent or 0),
            quantity=ci.item_quantity,
        )
        for ci in cart_items
        ])

        return order

    @staticmethod
    @transaction.atomic
    def mark_order_paid(order: Order) -> Order:
        """
        Mark an order and its cart as paid.

        Validates cart state and item existence before updating statuses.
        Safe to call multiple times without duplicating effects.
        """
        if order.status == "paid":
            return order

        cart = order.cart

        if cart.status != "pending":
            raise ValidationError("Cart must be confirmed before payment.")

        if not cart.items.exists():
            raise ValidationError("Cannot mark order as paid with an empty cart.")

        order.status = "paid"
        order.save(update_fields=["status"])

        cart.status = "paid"
        cart.save(update_fields=["status"])

        return order

    @staticmethod
    def cancel_unpaid_orders(self):
        """
        Cancels orders stuck in `awaiting_payment` beyond the configured payment TTL.

        Orders older than `ORDER_PAYMENT_TTL_HOURS` are cancelled via
        `OrderService.cancel_order` to enforce proper state transitions
        and side effects.

        Transient infrastructure errors trigger a retry.
        Logic errors fail fast without retry.
        """
        try:
            ORDER_PAYMENT_TTL_HOURS = settings.ORDER_PAYMENT_TTL_HOURS
            expiry_time = timezone.now() - timedelta(hours=ORDER_PAYMENT_TTL_HOURS)

            orders = Order.objects.filter(
                status="awaiting_payment",
                created_at__lt=expiry_time,
            )

            if orders:
                logger.info("Found %s orders to invalidate", orders.count())
                count = 0
                
                for order in orders.iterator():
                    if OrderService.cancel_order(order, reason="Payment TTL exceeded"):
                        count+=1
                    
                logger.info(f"Orders Invalidation Completed for {count} users")

        except (OperationalError, RedisConnectionError, KombuOperationalError) as exc:
            # Transient infra issue → retry
            logger.error(
                "Transient failure in cancel_unpaid_orders",
                exc_info=True,
            )
            raise self.retry(exc=exc, countdown=45)

        except Exception:
            # Programming / logic error → fail once, loudly
            logger.critical(
                "Fatal error in cancel_unpaid_orders - not retrying",
                exc_info=True,
            )
            raise