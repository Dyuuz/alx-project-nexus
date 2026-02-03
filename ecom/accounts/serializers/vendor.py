from rest_framework import serializers
from accounts.models import Vendor


class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Vendor instance.

    Automatically associates the vendor with the currently authenticated user.
    """
    class Meta:
        model = Vendor
        fields = (
            "id",
            "business_name",
            "business_address",
            "verified",
            "updated_at",
        )
        read_only_fields = ("id", "verified", "updated_at")
        
    def validate(self, attrs):
        """
        Validate the incoming data for creating a Vendor profile.

        Args:
            attrs (dict): The incoming data to validate.

        Raises:
            serializers.ValidationError: _description_

        Returns:
            _type_: _description_
        """
        user = self.context["request"].user

        if user.role == "vendor":
            raise serializers.ValidationError(
                "User role must not be 'vendor' to create Vendor profile"
            )

        return attrs


    def create(self, validated_data):
        """
        Create a new Vendor instance.

        Associates the new vendor with the currently authenticated user
        (from request context) before saving.

        Args:
            validated_data (dict): Validated input data.

        Returns:
            Vendor: The newly created Vendor instance.
        """
        request = self.context["request"]
        validated_data["user"] = request.user
        return super().create(validated_data)
    

class VendorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing Vendor instance.

    Only allows updating the vendor's business details, not read-only fields.
    """
    class Meta:
        model = Vendor
        fields = (
            "business_name",
            "business_address",
        )
        read_only_fields = ("id", "verified", "updated_at")


    def update(self, instance, validated_data):
        """
        Update a Vendor instance with validated data.

        Args:
            instance (Vendor): The Vendor instance to update.
            validated_data (dict): The validated input data.

        Returns:
            Vendor: The updated Vendor instance.
        """
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    
class VendorReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Vendor instances.

    Returns vendor information including verification status and last update timestamp.
    """
    class Meta:
        model = Vendor
        fields = [
            "business_name",
            "business_address",
            "verified",
            "updated_at",
        ]