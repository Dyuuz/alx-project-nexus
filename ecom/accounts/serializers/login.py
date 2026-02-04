from rest_framework import serializers
import re

class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login.

    Validates user input for login, including:
        - Email format using a regex.
        - Password length and complexity (must contain at least one digit).

    Fields:
        email (str): The user's email address.
        password (str): The user's password (write-only).

    Validation is performed before attempting authentication.
    """
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    def validate_email(self, value):
        if not re.match(self.EMAIL_REGEX, value):
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value