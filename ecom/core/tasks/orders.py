from django.core.mail import send_mail
from django.conf import settings

def send_order_confirmation_email(order):
    """
    Sends an order confirmation email to the customer.
    """
    subject = f"Order Confirmation - #{order.reference}"
    message = (
        f"Hi {order.customer.first_name},\n\n"
        f"Your order has been successfully placed.\n\n"
        f"Order Reference: {order.reference}\n"
        f"Total Amount: {order.total_amount}\n\n"
        f"Thank you for shopping with us."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.customer.email],
        fail_silently=False,
    )
    