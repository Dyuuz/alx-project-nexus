from rest_framework import serializers
from cart.models import Cart
from django.contrib.auth import get_user_model
from cart.serializers.cartItem import CartItemSerializer

User = get_user_model()

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for representing a Cart instance.

    Includes all cart items as a nested, read-only list and exposes the
    computed total amount of the cart. Certain fields are marked as
    read-only to prevent direct modification through the API.
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = (
            "id",
            "status",
            "items",
            "total_amount",
            "updated_at",
        )
        read_only_fields = ("status",)
