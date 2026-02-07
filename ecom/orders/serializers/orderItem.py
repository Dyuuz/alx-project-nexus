from rest_framework import serializers
from orders.models import OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product_id", "product_name", "unit_price", "discount_percent", "quantity", "line_total")

