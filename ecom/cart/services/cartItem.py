from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem
from products.models import Product


class CartService:
    """
    Service layer responsible for managing cart operations.

    Encapsulates all business rules related to cart creation,
    modification, and item management to ensure consistency
    across all entry points.
    """
    
    @staticmethod
    def get_or_create_cart(user):
        """
        Retrieve an existing unpaid cart for the user or create one if none exists.

        Ensures that a user has at most one active (unpaid) cart at any time.
        """
        cart, _ = Cart.objects.get_or_create(
            customer=user,
            status="unpaid"
        )
        return cart

    @staticmethod
    @transaction.atomic
    def add_item(cart: Cart, product_id, quantity=1):
        """
        Add a product to the cart or increase its quantity if it already exists.

        Prevents modification if the cart is no longer unpaid and guarantees
        atomicity of the operation.
        """
        if cart.status != "unpaid":
            raise ValidationError("This cart can no longer be modified.")

        product = get_object_or_404(Product, id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"item_quantity": quantity},
        )

        if not created:
            cart_item.item_quantity += quantity
            cart_item.save()

        return cart_item

    @staticmethod
    @transaction.atomic
    def update_item(cart: Cart, cart_item_id, quantity):
        """
        Update the quantity of a specific cart item.

        Deletes the item if the quantity is zero or less and blocks
        updates if the cart is no longer unpaid.
        """
        if cart.status != "unpaid":
            raise ValidationError("This cart can no longer be modified.")

        if quantity is None:
            raise ValidationError("Item quantity is required.")

        cart_item = get_object_or_404(
            CartItem, id=cart_item_id, cart=cart
        )

        if quantity <= 0:
            cart_item.delete()
            return None

        cart_item.item_quantity = quantity
        cart_item.save()
        return cart_item


    @staticmethod
    @transaction.atomic
    def remove_item(cart: Cart, cart_item_id):
        """
        Remove a cart item from the cart.

        Ensures the cart is still unpaid before allowing deletion.
        """
        if cart.status != "unpaid":
            raise ValidationError("This cart can no longer be modified.")

        cart_item = get_object_or_404(
            CartItem, id=cart_item_id, cart=cart
        )
        cart_item.delete()
