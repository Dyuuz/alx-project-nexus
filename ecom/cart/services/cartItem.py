from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from products.models import Product
from cart.services.cart_guards import assert_cart_is_modifiable
from django.utils import timezone


class CartItemService:
    """
    Service layer responsible for managing cart operations.

    Encapsulates all business rules related to cart creation,
    modification, and item management to ensure consistency
    across all entry points.
    """

    @staticmethod
    @transaction.atomic
    def add_item(cart: Cart, product_id, quantity=1):
        """
        Add a product to the cart or increase its quantity if it already exists.

        Prevents modification if the cart is no longer unpaid and guarantees
        atomicity of the operation.
        """
        assert_cart_is_modifiable(cart)
        
        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"item_quantity": quantity},
        )

        if not created:
            cart_item.append_quantity(quantity)
        
        CartItemService.record_cart_activity(cart)
        
        append = True if not created else False

        return cart_item, append

    @staticmethod
    @transaction.atomic
    def update_item(cart: Cart, cart_item_id, quantity):
        """
        Update the quantity of a cart item.

        - Only unpaid carts can be modified
        - Quantity must be provided
        - Item is removed if quantity <= 0
        - User activity is recorded on successful mutation
        """
        assert_cart_is_modifiable(cart)

        if quantity is None:
            raise ValidationError("Item quantity is required.")

        cart_item = get_object_or_404(
            CartItem,
            id=cart_item_id,
            cart=cart,
        )

        if quantity <= 0:
            cart_item.delete()
            CartItemService.record_cart_activity(cart)
            return None
        
        if cart_item.item_quantity == quantity:
            return

        cart_item.item_quantity = quantity
        cart_item.save(update_fields=["item_quantity"])

        CartItemService.record_cart_activity(cart)

        return cart_item

    @staticmethod
    @transaction.atomic
    def remove_item(cart: Cart, cart_item_id):
        """
        Remove a cart item from the cart.

        Ensures the cart is still unpaid before allowing deletion.
        """
        assert_cart_is_modifiable(cart)

        cart_item = get_object_or_404(
            CartItem, id=cart_item_id, cart=cart
        )
        cart_item.delete()

        CartItemService.record_cart_activity(cart)
        
    @staticmethod
    def record_cart_activity(cart):
        """
        
        """
        cart.last_activity_at = timezone.now()
        cart.save(update_fields=["last_activity_at"])