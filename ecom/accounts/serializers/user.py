from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new User instance.

    Handles creating a user with a hashed password and validates
    minimum password length.
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
            "role",
        )

    def create(self, validated_data):
        """
        Create and return a new User instance.

        Uses `create_user` method from the User model to ensure
        the password is properly hashed.

        Args:
            validated_data (dict): Validated input data.

        Returns:
            User: The newly created user instance.
        """
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing User instance.

    Allows updating user details, including password.
    If a new password is provided, it is hashed before saving.
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
            "is_active",
        )

    def update(self, instance, validated_data):
        """
        Update the User instance with validated data.

        Handles password separately to ensure it is hashed.

        Args:
            instance (User): The user instance to update.
            validated_data (dict): Validated input data.

        Returns:
            User: The updated user instance.
        """
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


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
