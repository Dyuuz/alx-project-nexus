from django.db import transaction
from cart.models import Cart
from rest_framework.exceptions import ValidationError


class CartService:
    """
    Service layer responsible for managing cart operations.
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