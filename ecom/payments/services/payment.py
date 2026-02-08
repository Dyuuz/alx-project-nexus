import uuid
from django.db import transaction
from rest_framework.exceptions import ValidationError
from payments.models import Payment
from orders.models import Order
from orders.services.order import OrderService


class PaymentService:
    """
    Handles payment initiation and confirmation for orders.
    """
    
    @staticmethod
    @transaction.atomic
    def initiate_payment(order: Order, provider: str = "internal") -> Payment:
        """
        Initiate a payment for an order.

        Creates a pending payment record if the order is eligible
        and ensures idempotency by returning an existing payment
        when applicable.
        """
        existing_payment = Payment.objects.filter(order=order, status="paid").first()
        if existing_payment:
            return existing_payment # idempotent
        
        if order.status not in ["awaiting_payment", "created"]:
            raise ValidationError("Order is not eligible for payment.")

        if hasattr(order, "payment"):
            return order.payment  # idempotent

        reference = uuid.uuid4().hex
        payment = Payment.objects.create(
            order=order,
            amount=order.total_amount,
            provider=provider,
            reference=reference,
            status="pending",
        )
        return payment

    @staticmethod
    @transaction.atomic
    def confirm_payment(reference: str) -> Payment:
        """
        Confirm a payment using its reference.

        Marks the payment as paid and updates the related
        order and cart states accordingly.
        """
        try:
            payment = Payment.objects.select_for_update().get(reference=reference)
        except:
            raise ValidationError("Provide a valid reference no")

        if payment.status == "paid":
            return payment

        # Real integration with payment provider using reference for verification.
        
        payment.status = "paid"
        payment.save(update_fields=["status"])

        # move order + cart to paid
        OrderService.mark_order_paid(payment.order)

        return payment
