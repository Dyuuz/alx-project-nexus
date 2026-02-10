from rest_framework import serializers
from cart.models import Checkout
from cart.serializers.cart import CartSerializer

class CheckoutSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a checkout record from an active cart.

    Validates that the associated cart contains at least one item
    before allowing the checkout process to proceed.
    """
    
    class Meta:
        model = Checkout
        fields = (
            "id",
            "cart",
            "shipping_address",
            "billing_address",
            "payment_method",
            "created_at",
        )
        read_only_fields = ("id", "cart", "created_at")

    def validate(self, attrs):
        """
        Ensure the cart is not empty before checkout.
        """
        cart = self.context["cart"]

        if not cart.items.exists():
            raise serializers.ValidationError(
                "Cannot proceed to checkout with an empty cart."
            )

        return attrs


class ConfirmCheckoutSerializer(serializers.Serializer):
    """
    Validates the cart ID required to confirm a checkout.
    """
    cart_id = serializers.UUIDField()
    

class CheckoutHistorySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for checkout history.
    """

    cart = CartSerializer(read_only=True)

    class Meta:
        model = Checkout
        fields = (
            "id",
            "created_at",
            "updated_at",
            "cart",
        )