from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

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

        except ValidationError:
            Cart.objects.filter(id=cart.id).update(status="unpaid")
            raise
    
    @staticmethod
    @transaction.atomic
    def create_order_from_confirmed_checkout(cart: Cart) -> Order:
        """
        Creates an order only when cart is pending (checkout confirmed).
        Snapshots pricing & product info into OrderItems.
        """
        if cart.status != "pending":
            raise ValidationError("Cart must be confirmed before creating an order.")

        if hasattr(cart, "order"):
            return cart.order  # idempotent

        if not hasattr(cart, "checkout"):
            raise ValidationError("Checkout does not exist for this cart.")

        checkout: Checkout = cart.checkout

        if not cart.items.exists():
            raise ValidationError("Cannot create an order from an empty cart.")

        # Lock cart items rows for consistent read
        cart_items = CartItem.objects.select_for_update().filter(cart=cart).select_related("product")
        
        for item in cart_items:
            product: Product = item.product

            if hasattr(product, "stock"):
                if item.item_quantity > product.stock:
                    raise ValidationError(f"Insufficient stock for {getattr(product, 'name', 'product')}.")


        order = Order.objects.create(
            customer=cart.customer,
            cart=cart,
            status="awaiting_payment",
            shipping_address=checkout.shipping_address,
            billing_address=checkout.billing_address or checkout.shipping_address,
            payment_method=checkout.payment_method,
        )

        # Snapshot each item
        bulk_items = []
        for ci in cart_items:
            p = ci.product
            bulk_items.append(
                OrderItem(
                    order=order,
                    product_id=p.id,
                    product_name=getattr(p, "name", "Product"),
                    unit_price=p.original_price,
                    discount_percent=int(getattr(p, "discount_percent", 0) or 0),
                    quantity=ci.item_quantity,
                )
            )
        OrderItem.objects.bulk_create(bulk_items)

        return order

    @staticmethod
    @transaction.atomic
    def mark_order_paid(order: Order) -> Order:
        if order.status == "paid":
            return order
        order.status = "paid"
        order.save(update_fields=["status"])
        # Mark cart as paid too (optional but consistent)
        cart = order.cart
        cart.status = "paid"
        cart.save(update_fields=["status"])
        return order
