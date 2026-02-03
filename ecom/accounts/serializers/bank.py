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


    def create(self, validated_data):
        """
        Create a new BankAccount instance.

        Associates the new bank account with the currently authenticated vendor
        before saving.
        """
        request = self.context["request"]

        try:
            vendor = request.user.vendor_profile  # ✅ get Vendor instance
        except Vendor.DoesNotExist:
            raise serializers.ValidationError("User is not a vendor")

        validated_data["vendor"] = vendor  # ✅ assign Vendor instance
        return super().create(validated_data)


    def validate(self, attrs):
        """
        Validate that the bank account number is unique per vendor.

        If updating an existing instance, it excludes the current instance
        from the uniqueness check.
        
        Args:
            attrs (dict): The input data for validation.
        
        Raises:
            serializers.ValidationError: If a bank account with the same number
            already exists for the vendor.
        
        Returns:
            dict: The validated input data.
        """
        vendor = self.instance.vendor if self.instance else attrs.get("vendor")
        number = self.instance.number if self.instance else attrs.get("number")

        # Exclude current instance from uniqueness check
        qs = BankAccount.objects.filter(vendor=vendor, number=number)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        if qs.exists():
            raise serializers.ValidationError("Bank account already exists for this vendor.")
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