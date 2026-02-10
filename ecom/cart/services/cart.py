from django.db import transaction
from cart.models import Cart
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError
from django.conf import settings
from django.db import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError
from kombu.exceptions import OperationalError as KombuOperationalError

import logging
logger = logging.getLogger(__name__)


class CartService:
    """
    Service layer responsible for managing cart lifecycle operations.
    """
    @staticmethod
    @transaction.atomic
    def expire_cart(cart, reason: str):
        """
        Expires a cart unless it is already paid or expired.

        Marks the cart as invalid with the provided reason.
        """
        if cart.status in ("paid", "expired"):
            return

        cart.invalidate(reason=reason)
        return True

    @staticmethod
    @transaction.atomic
    def get_or_create_cart(user):
        """
        Returns an active cart for the user or creates a new one.

        Reuses recent unpaid or pending carts within the configured TTL.
        """
        CART_TTL_HOURS = settings.CART_TTL_HOURS
        expiry_time = timezone.now() - timedelta(hours=CART_TTL_HOURS)

        cart = (
            Cart.objects
            .select_for_update()
            .filter(
                customer=user,
                status__in=("unpaid", "pending"),
                last_activity_at__gte=expiry_time,
            )
            .order_by("-last_activity_at")
            .first()
        )

        if cart:
            return cart

        return Cart.objects.create(
            customer=user,
            status="unpaid",
            last_activity_at=timezone.now(),
        )
        
    @staticmethod
    def cleanup_abandoned_carts(self):
        """
        Expires carts that have been inactive beyond the configured TTL.

        Designed to run periodically and safely invalidate abandoned carts.
        """
        try:
            CART_TTL_HOURS = settings.CART_TTL_HOURS
            expiry_time = timezone.now() - timedelta(hours=CART_TTL_HOURS)

            carts = Cart.objects.filter(
                status__in=("unpaid", "pending"),
                last_activity_at__lt=expiry_time,
            )
            
            if carts:
                logger.info("Found %s carts to invalidate", carts.count())
                count = 0
                
                for cart in carts.iterator():
                    if CartService.expire_cart(cart, reason="Cart inactive beyond TTL"):
                        count+=1
                    
                logger.info(f"Carts Invalidation Completed for {count} users")
                
        except (OperationalError, RedisConnectionError, KombuOperationalError) as exc:
            logger.error("Transient failure in cleanup_abandoned_carts", exc_info=True)
            raise self.retry(exc=exc, countdown=45)
        
        except Exception:
            logger.critical(
                "Fatal error in cleanup_abandoned_carts - not retrying",
                exc_info=True,
            )
            raise
