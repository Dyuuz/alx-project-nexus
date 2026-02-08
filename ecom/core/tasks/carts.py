from cart.models import Cart
from time import timezone
from datetime import timedelta

def cleanup_abandoned_carts():
    """
    Deletes or archives carts inactive for a long period.
    """
    expiry_time = timezone.now() - timedelta(days=7)

    abandoned_carts = Cart.objects.filter(
        is_active=True,
        updated_at__lt=expiry_time,
    )

    for cart in abandoned_carts:
        cart.mark_abandoned()