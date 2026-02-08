from django.core.mail import mail_admins

def alert_admin_failed_payment(payment, reason: str):
    """
    Notify admins when a payment fails.
    """
    subject = "🚨 Payment Failure Alert"
    message = (
        f"Payment failed.\n\n"
        f"Payment Ref: {payment.reference}\n"
        f"Order Ref: {payment.order.reference}\n"
        f"Reason: {reason}"
    )

    mail_admins(subject, message)
