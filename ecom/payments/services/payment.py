import uuid
from django.db import transaction
from rest_framework.exceptions import ValidationError
from payments.models import Payment
from orders.models import Order

from asgiref.sync import async_to_sync
from core.utils.mail_sender import send_mail_helper
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from django.db import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError
from kombu.exceptions import OperationalError as KombuOperationalError

import logging
logger = logging.getLogger(__name__)


class PaymentService:
    """
    Handles payment initiation and confirmation for orders.
    """

    NON_MODIFIABLE_CART_STATES = {
        "paid": "This cart has already been paid and cannot be modified.",
        "expired": "This cart is no longer active.",
        "unpaid": "This cart is still active and cannot be proceesed for payment.",
    }

    def assert_cart_is_valid(cart, *, allow_admin_override=False):
        """
        Ensures the cart can be modified.

        By default, only unpaid carts are modifiable.
        Admin override must be explicitly allowed.
        """
        message = PaymentService.NON_MODIFIABLE_CART_STATES.get(cart.status)

        if message:
            if allow_admin_override:
                return
            raise ValidationError(message)

    
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
        
        PaymentService.assert_cart_is_valid(order.cart)
        
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
        from orders.services.order import OrderService
        
        try:
            payment = Payment.objects.select_for_update().get(reference=reference)
        except:
            raise ValidationError("Provide a valid reference no")

        if payment.status == "paid":
            return payment
        
        if payment.status == "failed":
            raise ValidationError("Payment failed, pls try again.")

        # Real integration with payment provider using reference for verification.
        # PayStack/Stripe/PayPal
        
        payment.status = "paid"
        payment.save(update_fields=["status"])

        # move order + cart to paid
        OrderService.mark_order_paid(payment.order)
        message = "Your payment is confirmed"
        
        if async_to_sync(send_mail_helper)(message, payment.order.customer.email):
            payment.payment_alert = True
            payment.save(update_fields=["payment_alert"])
            
        return payment
    
    @staticmethod
    @transaction.atomic
    def send_payment_alerts(self):
        """
        Sends payment confirmation emails for paid payments
        that have not yet received an alert.
        """
        try:
            payments = Payment.objects.filter(
                status="paid",
                payment_alert=False,
            )

            if payments:
                logger.info("Found %s payments alert message to deliver.", payments.count())
                count = 0
                
                for payment in payments.iterator():
                    
                    if async_to_sync(send_mail_helper)():
                        payment.payment_alert = True
                        payment.save(update_fields=["payment_alert"])
                        count+=1
                
                logger.info(f"Mail Successfully Delivered to - {count} users")

        except (OperationalError, RedisConnectionError, KombuOperationalError) as exc:
            logger.error(
                "Transient failure in send_payment_alerts",
                exc_info=True,
            )
            raise self.retry(exc=exc, countdown=45)

        except Exception:
            logger.critical(
                "Fatal error in send_payment_alerts - not retrying",
                exc_info=True,
            )
            raise
        
    @staticmethod
    @transaction.atomic
    def send_payment_reminder_24h(self):
        """
        Sends a payment reminder to customers with orders still
        awaiting payment after the configured 24-hour threshold.
        """
        try:
            PAYMENT_REMINDER_24H_TTL_HOURS = settings.PAYMENT_REMINDER_24H_TTL_HOURS
            cutoff = timezone.now() - timedelta(hours=PAYMENT_REMINDER_24H_TTL_HOURS)

            orders = Order.objects.filter(
                status="awaiting_payment",
                created_at__lte=cutoff,
                payment_reminder_sent=False,
            )
            
            if orders:
                logger.info("Found %s orders to push mail reminders to - ", orders.count())
                count = 0
                
                for order in orders.iterator():
                    if async_to_sync(send_mail_helper)():
                        order.payment_reminder_sent = True
                        order.save(update_fields=["payment_reminder_sent"])
                        count+=1
                    
                logger.info(f"Mail Successfully Delivered to - {count} users")
            
        except (OperationalError, RedisConnectionError, KombuOperationalError) as exc:
            logger.error("Transient failure in cleanup_abandoned_carts", exc_info=True)
            raise self.retry(exc=exc, countdown=45)
        
        except Exception:
            logger.critical(
                "Fatal error in cleanup_abandoned_carts - not retrying",
                exc_info=True,
            )
            raise
    
    
    @staticmethod
    @transaction.atomic
    def send_final_payment_reminder(self):
        """
        Sends a final payment reminder within the configured
        time window before an unpaid order expires.
        """
        try:
            now = timezone.now()
            FINAL_PAYMENT_REMINDER_TTL_HOURS_START = settings.FINAL_PAYMENT_REMINDER_TTL_HOURS_START
            FINAL_PAYMENT_REMINDER_TTL_HOURS_END = settings.FINAL_PAYMENT_REMINDER_TTL_HOURS_END
            
            start = now - timedelta(hours=FINAL_PAYMENT_REMINDER_TTL_HOURS_END)
            end = now - timedelta(hours=FINAL_PAYMENT_REMINDER_TTL_HOURS_START)

            orders = Order.objects.filter(
                status="awaiting_payment",
                created_at__gte=start,
                created_at__lte=end,
                final_payment_reminder_sent=False,
            )
            
            if orders:
                logger.info("Found %s orders to push mail reminders to - ", orders.count())
                count = 0
                
                for order in orders.iterator():
                    if  async_to_sync(send_mail_helper)():
                        order.final_payment_reminder_sent = True
                        order.save(update_fields=["final_payment_reminder_sent"])
                        count+=1
                
                logger.info(f"Mail Successfully Delivered to - {count} users")
            
        except (OperationalError, RedisConnectionError, KombuOperationalError) as exc:
            logger.error("Transient failure in cleanup_abandoned_carts", exc_info=True)
            raise self.retry(exc=exc, countdown=45)
        
        except Exception:
            logger.critical(
                "Fatal error in cleanup_abandoned_carts - not retrying",
                exc_info=True,
            )
            raise
