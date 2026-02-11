from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.throttling import ScopedRateThrottle

from payments.models import Payment
from payments.serializers.payment import (
    PaymentReadSerializer, PaymentInitiateSerializer, 
    PaymentConfirmSerializer
)
from core.permissions import IsPaymentOwnerOrAdmin, IsCustomer
from payments.services.payment import PaymentService
from orders.models import Order


class PaymentViewSet(ModelViewSet):
    """
    Handles payment retrieval, initiation, and confirmation.

    Allows customers to initiate and confirm payments for their orders,
    while admins can view all payment records.
    """
    
    queryset = Payment.objects.all()
    serializer_class = PaymentReadSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "post"]
    throttle_classes = [ScopedRateThrottle]
    
    list_message = "Payments history retrieved successfully."

    def get_queryset(self):
        """
        Return payments visible to the requesting user.

        - Admin users can access all payments.
        - Customers can only access payments linked to their orders.
        """
        user = self.request.user
        if getattr(user, "is_staff", False):
            return Payment.objects.all()
        return Payment.objects.filter(order__customer=user)
    
    
    def get_throttles(self):
        if self.action in ["list", "retrieve"]:
            self.throttle_scope = "payment_read"

        elif self.action == "initiate":
            self.throttle_scope = "payment_initiate"

        elif self.action == "confirm":
            self.throttle_scope = "payment_confirm"

        return super().get_throttles()


    def get_permissions(self):
        """
        Apply permissions based on the current action.

        - Listing and retrieval require ownership or admin access.
        - Payment initiation and confirmation are restricted to customers.
        """
        
        if self.action in ["list"]:
            return [IsAuthenticated(), IsPaymentOwnerOrAdmin()]
        if self.action in ["initiate", "confirm"]:
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Select the appropriate serializer for the action.

        Uses write serializers for payment initiation and confirmation,
        and a read serializer for all other actions.
        """
        
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

        Initiate a payment for an order.

        Validates the request data, ensures the order belongs to the
        authenticated user, and creates a pending payment record.
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
        
        Confirm a payment using its reference.

        Marks the payment as paid and updates the related
        order and cart states.
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
