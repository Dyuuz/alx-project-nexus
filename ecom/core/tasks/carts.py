from cart.models import Cart
from time import timezone
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from cart.services.cart import CartService

# Cart Tasks

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def cleanup_abandoned_carts(ttl_minutes=settings.CART_TTL_MINUTES):
    expiry_time = timezone.now() - timedelta(minutes=ttl_minutes)

    carts = Cart.objects.filter(
        status__in=("unpaid", "pending"),
        last_activity_at__lt=expiry_time,
    )

    for cart in carts.iterator():
        CartService.expire_cart(cart, reason="Cart inactive beyond TTL")