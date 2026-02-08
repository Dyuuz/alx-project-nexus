from rest_framework import serializers
from payments.models import Payment


class PaymentReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading payment details.

    Returns payment information related to an order.
    All fields are read-only.
    """

    class Meta:
        model = Payment
        fields = ("id", "order", "amount", "provider", "reference", "status", "created_at")
        read_only_fields = fields


class PaymentInitiateSerializer(serializers.Serializer):
    """
    Validates data required to initiate a payment.
    """
    
    order_id = serializers.UUIDField(required=True)
    provider = serializers.CharField(required=False, default="internal")


class PaymentConfirmSerializer(serializers.Serializer):
    """
    Validates the payment reference used to confirm a payment.
    """
    reference = serializers.CharField(required=True)
    