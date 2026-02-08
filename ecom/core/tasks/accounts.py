from django.core.mail import mail_admins

def alert_admin_low_stock(product):
    """
    Notify admins when product stock is critically low.
    """
    if product.stock > product.low_stock_threshold:
        return

    subject = "⚠ Low Stock Alert"
    message = (
        f"Product '{product.name}' is running low.\n\n"
        f"Current Stock: {product.stock}\n"
        f"Threshold: {product.low_stock_threshold}"
    )

    mail_admins(subject, message)
