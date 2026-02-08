from rest_framework import serializers
from orders.models import Order
from orders.serializers.orderItem import OrderItemReadSerializer


class OrderCreateFromCheckoutSerializer(serializers.Serializer):
    """
    No body required by default; kept for extensibility (e.g. promo_code).
    """
    pass


class OrderReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading order details.

    Returns order information along with its items and calculated total
    amount. All fields are read-only and intended for response output only.
    """
    items = OrderItemReadSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "shipping_address",
            "billing_address",
            "payment_method",
            "created_at",
            "items",
            "total_amount",
        )

class CreateOrderSerializer(serializers.Serializer):
    """
    Validates the cart ID required to create an order.
    """
    cart_id = serializers.UUIDField()