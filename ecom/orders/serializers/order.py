from rest_framework import serializers
from orders.models import Order
from orders.serializers.orderItem import OrderItemReadSerializer


class OrderCreateFromCheckoutSerializer(serializers.Serializer):
    """
    No body required by default; kept for extensibility (e.g. promo_code).
    """
    pass


class OrderReadSerializer(serializers.ModelSerializer):
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
