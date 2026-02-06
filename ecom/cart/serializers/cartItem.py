from rest_framework import serializers
from cart.models import CartItem
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and representing items within a cart.

    Accepts a product identifier when creating a cart item, exposes the
    related product as a read-only field, and computes the total amount
    based on item quantity and product price.
    """
    
    product_id = serializers.UUIDField(write_only=True)
    product = serializers.StringRelatedField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product",
            "product_id",
            "item_quantity",
            "total_amount",
        )

    def validate_item_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

class CartItemUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating the quantity of an existing cart item.

    Limits updates strictly to the item quantity and ensures
    the value is non-negative.
    """
    item_quantity = serializers.IntegerField(min_value=0)