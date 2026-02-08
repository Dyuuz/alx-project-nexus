# services/notifications/payment_receipt.py

def send_payment_receipt(payment):
    """
    Sends a payment receipt after successful payment.
    """
    subject = f"Payment Receipt - {payment.reference}"
    message = (
        f"Hello {payment.customer.first_name},\n\n"
        f"We have received your payment.\n\n"
        f"Payment Reference: {payment.reference}\n"
        f"Order: {payment.order.reference}\n"
        f"Amount Paid: {payment.amount}\n"
        f"Payment Method: {payment.method}\n\n"
        f"This email serves as your receipt."
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [payment.customer.email],
    )
