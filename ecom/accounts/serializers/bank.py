from rest_framework import serializers
from accounts.models import BankAccount, Vendor

class BankAccountCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a BankAccount instance.

    Automatically associates the bank account with the requesting user (vendor)
    and ensures that a vendor cannot have duplicate accounts with the same number.
    """
    class Meta:
        model = BankAccount
        fields = (
            "id",
            "number",
            "name",
            "bank_name",
            "bank_code",
            "subaccount_code",
        )
        read_only_fields = ("id", "verified", "updated_at")
        extra_kwargs = {
            'number': {'validators': []},
            'subaccount_code': {'validators': []},
        }

    def create(self, validated_data):
        """
        Create a new BankAccount instance.

        Associates the new bank account with the currently authenticated vendor
        before saving.
        """
        request = self.context["request"]
        vendor = request.user.vendor_profile
        validated_data["vendor"] = vendor
        return super().create(validated_data)

    def validate(self, attrs):
        """
        Validate the user role before creating a BankAccount.
        - Reject customers entirely.
        - Allow vendors only if they don't already have a bank account.
        """
        request = self.context['request']
        user = request.user

        # Reject customers
        if user.role == "customer":
            raise serializers.ValidationError(
                "Customers are not allowed to create bank accounts."
            )

        # Only allow vendors
        if user.role == "vendor":
            try:
                vendor = user.vendor_profile
            except Vendor.DoesNotExist:
                raise serializers.ValidationError("User is not a vendor.")

            # Check if this vendor already has a bank account
            if BankAccount.objects.filter(vendor=vendor).exists():
                raise serializers.ValidationError(
                    "Oops! A bank account for you already exists."
                )
        return attrs

    
class BankAccountUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing BankAccount instance.

    Only allows updating the account details, not the read-only fields.
    """
    class Meta:
        model = BankAccount
        fields = (
            "number",
            "name",
            "bank_name",
            "bank_code",
            "subaccount_code",
        )
        read_only_fields = ("id", "verified", "updated_at")

    def update(self, instance, validated_data):
        """
        Update an existing BankAccount instance with validated data.
        
        Args:
            instance (BankAccount): The instance to update.
            validated_data (dict): The validated input data.
        
        Returns:
            BankAccount: The updated BankAccount instance.
        """
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
    

class BankAccountReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading BankAccount instances.

    Returns all account fields, including read-only fields like 'verified'
    and 'updated_at'.
    """
    class Meta:
        model = BankAccount
        fields = [
            "id",
            "number",
            "name",
            "bank_name",
            "bank_code",
            "subaccount_code",
            "verified",
            "updated_at",
        ]