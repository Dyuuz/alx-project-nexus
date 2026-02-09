from cart.models import Cart
from django.utils import timezone
from datetime import timedelta
from celery import shared_task
from django.conf import settings
from cart.services.cart import CartService
import logging

logger = logging.getLogger(__name__)

# Cart Tasks

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 45})
def cleanup_abandoned_carts(self):
    ttl_minutes = settings.CART_TTL_MINUTES
    expiry_time = timezone.now() - timedelta(minutes=ttl_minutes)
    logger.info("Cart cleanup expiry time: %s", expiry_time)

    carts = Cart.objects.filter(
        status__in=("unpaid", "pending"),
        last_activity_at__lt=expiry_time,
    )
    
    if carts:
        for cart in carts.iterator():
            logger.info("Expiring cart %s with status %s", cart.id, cart.status)
            CartService.expire_cart(cart, reason="Cart inactive beyond TTL")