from rest_framework import serializers


class EmailVerif_ResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()