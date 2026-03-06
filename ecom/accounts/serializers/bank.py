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
            "number",
            "bank_name",
        )
        read_only_fields = ("id", "name", "verified", "updated_at")
        extra_kwargs = {
            'number': {'validators': []},
        }

    def validate(self, attrs):
        """
        Validate the user role before creating a BankAccount.
        - Reject customers entirely.
        - Allow vendors only if they don't already have a bank account.
        """
        request = self.context['request']
        user = request.user
        
        vendor = user.vendor_profile

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
            "bank_name",
        )
        read_only_fields = ("id", "verified", "updated_at")
    

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
            "updated_at",
        ]