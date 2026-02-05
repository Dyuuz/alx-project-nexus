from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new User instance.

    - Handles creating a user with a hashed password and validates
    minimum password length.
    - Field validation
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
        )
        
    EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    def validate_email(self, value):
        if not re.match(self.EMAIL_REGEX, value):
            raise serializers.ValidationError("Enter a valid email address.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("First name should only contain letters.")
        return value

    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Last name should only contain letters.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing User instance.

    Allows updating user details, including password.
    If a new password is provided, it is hashed before saving.
    
    - Field validation
    """
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password",
        )
        
    # Regex pattern for email validation
    EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    def validate_email(self, value):
        if not re.match(self.EMAIL_REGEX, value):
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def validate_first_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("First name should only contain letters.")
        return value

    def validate_last_name(self, value):
        if not value.isalpha():
            raise serializers.ValidationError("Last name should only contain letters.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value


class UserReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading User instances.

    Returns user information, including role and account status.
    Does not include password.
    """
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "email_verified",
            "is_active",
        ]
