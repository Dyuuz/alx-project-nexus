from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
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
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
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


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()  
    
class PasswordChangeVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    

class PasswordConfirmSerializer(serializers.Serializer):
    reset_token = serializers.CharField(required=False)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        
        if len(attrs["new_password"]) < 8 or len(attrs["confirm_password"]) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        
        if not any(char.isdigit() for char in attrs["new_password"]):
            raise serializers.ValidationError("Password must contain at least one digit.")

        validate_password(attrs["new_password"])
        
        # Require reset_token only for unauthenticated flow
        require_token = self.context.get("require_token", False)

        if require_token and not attrs.get("reset_token"):
            raise serializers.ValidationError(
                {"reset_token": "Reset token is required."}
            )
            
        return attrs


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


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()


class ResponseDataSerializer(serializers.Serializer):
    status = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()
    data = serializers.DictField()