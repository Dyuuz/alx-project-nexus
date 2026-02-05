from rest_framework import serializers
from products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "vendor",
            "image",
            "public_id",
            "srcURL",
            "description",
            "stock",
            "original_price",
            "discount_percent",
            "discount_amount",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "vendor",
            "discount_amount",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        return value.title().strip()

    def validate(self, attrs):
        original_price = (
            attrs.get("original_price")
            if "original_price" in attrs
            else getattr(self.instance, "original_price", None)
        )

        discount_percent = attrs.get(
            "discount_percent",
            getattr(self.instance, "discount_percent", 0)
        )

        if discount_percent and original_price is None:
            raise serializers.ValidationError(
                {"original_price": "Original price is required when applying a discount."}
            )

        return attrs
