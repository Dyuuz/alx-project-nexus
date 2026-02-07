from rest_framework import serializers
from payments.models import Payment


class PaymentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "order", "amount", "provider", "reference", "status", "created_at")
        read_only_fields = fields


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.CharField(required=False, default="internal")


class PaymentConfirmSerializer(serializers.Serializer):
    reference = serializers.CharField()
    
