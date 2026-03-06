from rest_framework import serializers
from accounts.models import Vendor


class VendorCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Vendor instance.

    Automatically associates the vendor with the currently authenticated user.
    """
    class Meta:
        model = Vendor
        fields = (
            "id",
            "business_id",
            "business_name",
            "business_address",
            "review_status",
            "activation_status",
            "updated_at",
        )
        read_only_fields = ("id", "review_status", "activation_status", "updated_at")

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

        if Vendor.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "A vendor profile already exists for this user."
            )

        return attrs
    

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
        read_only_fields = ("id", "business_id", "review_status", "activation_status", "updated_at")

    
class VendorReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Vendor instances.

    Returns vendor information including verification status and last update timestamp.
    """
    class Meta:
        model = Vendor
        fields = [
            "id",
            "business_id",
            "business_name",
            "business_address",
            "review_status",
            "activation_status",
            "updated_at",
        ]