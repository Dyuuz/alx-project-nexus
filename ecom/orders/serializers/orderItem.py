from rest_framework import serializers
from orders.models import OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading individual order items.

    Returns product details, pricing information, quantity, and the
    calculated line total for each item in an order.
    """
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product_id", "product_name", "unit_price", "discount_percent", "quantity", "line_total")

