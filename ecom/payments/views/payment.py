from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer

from payments.models import Payment
from payments.serializers.payment import (
    PaymentReadSerializer, PaymentInitiateSerializer, 
    PaymentConfirmSerializer
)
from payments.permissions import IsPaymentOwnerOrAdmin
from payments.services.payment import PaymentService
from orders.models import Order
from orders.permissions import IsCustomer


class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentReadSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_staff", False):
            return Payment.objects.all()
        return Payment.objects.filter(order__customer=user)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated(), IsPaymentOwnerOrAdmin()]
        if self.action in ["initiate", "confirm"]:
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "initiate":
            return PaymentInitiateSerializer
        if self.action == "confirm":
            return PaymentConfirmSerializer
        return PaymentReadSerializer

    @action(detail=False, methods=["post"], url_path="initiate")
    def initiate(self, request):
        """
        POST /payments/initiate/
        body: { "order_id": "...", "provider": "internal" }
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "code": "INVALID_REQUEST",
                    "message": "Invalid request data.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        order_id = serializer.validated_data["order_id"]

        order = Order.objects.get(id=order_id, customer=request.user)

        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data.get("provider", "internal")
        payment = PaymentService.initiate_payment(order, provider=provider)
        
        return Response(
            {
                "status": "success",
                "code": "PAYMENT_INITIATED",
                "message": "Payment initiated successfully.",
                "data": PaymentReadSerializer(payment).data,
            },
            status=status.HTTP_201_CREATED,
        )


    @action(detail=False, methods=["post"], url_path="confirm")
    def confirm(self, request):
        """
        POST /payments/confirm/
        body: { "reference": "..." }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = PaymentService.confirm_payment(serializer.validated_data["reference"])
        
        return Response(
            {
                "status": "success",
                "code": "PAYMENT_CONFIRMED",
                "message": "Payment confirmed successfully.",
                "data": PaymentReadSerializer(payment).data,
            },
            status=status.HTTP_200_OK,
        )
