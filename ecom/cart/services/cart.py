from django.db import transaction
from cart.models import Cart
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from rest_framework.exceptions import ValidationError


class CartService:
    """
    Service layer responsible for managing cart operations.
    """
    @staticmethod
    @transaction.atomic
    def expire_cart(cart, reason: str):
        """
        
        """
        if cart.status in ("paid", "expired"):
            return

        cart.invalidate(reason=reason)


    @staticmethod
    @transaction.atomic
    def get_or_create_cart(user):
        expiry_time = timezone.now() - timedelta(minutes=settings.CART_TTL_MINUTES)

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
