from rest_framework import serializers
from products.models import Category
from PIL import Image
import re

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image', 'slug', 'date', 'is_active']
        read_only_fields = ['id', 'slug', 'date', 'is_active']

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name is required.")
        
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Category name must be at least 2 characters long."
            )

        if not re.match(r'^[A-Za-z0-9 &\-]+$', value):
            raise serializers.ValidationError(
                "Category name can only contain letters, numbers, spaces, '&' and '-'."
            )

        return value.title()

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError("Image is required.")

        valid_formats = ['JPEG', 'JPG', 'PNG', 'WEBP']

        try:
            img = Image.open(image)
            if img.format.upper() not in valid_formats:
                raise serializers.ValidationError(
                    "Image must be PNG, JPG, JPEG, or WEBP format."
                )
        except Exception:
            raise serializers.ValidationError("Uploaded file is not a valid image.")

        # Optional: size limit (e.g. 500kb)
        max_size = 500 * 1024
        if image.size > max_size:
            raise serializers.ValidationError(
                "Image size must be less than 500KB."
            )

        return image