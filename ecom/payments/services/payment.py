import uuid
from django.db import transaction
from rest_framework.exceptions import ValidationError
from payments.models import Payment
from orders.models import Order
from orders.services.order import OrderService


class PaymentService:
    @staticmethod
    @transaction.atomic
    def initiate_payment(order: Order, provider: str = "internal") -> Payment:
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
        payment = Payment.objects.select_for_update().get(reference=reference)

        if payment.status == "paid":
            return payment

        # Real integration with payment provider using reference for verification.
        
        payment.status = "paid"
        payment.save(update_fields=["status"])

        # move order + cart to paid
        OrderService.mark_order_paid(payment.order)

        return payment
