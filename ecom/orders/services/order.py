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


class OrderService:
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
        
        for item in cart_items:
            product: Product = item.product

            if hasattr(product, "stock"):
                if item.item_quantity > product.stock:
                    print("err")
                    raise ValidationError(f"Insufficient stock for {getattr(product, 'name', 'product')}.")
                
            product.stock -= item.item_quantity
            product.save(update_fields=["stock"])
        
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

