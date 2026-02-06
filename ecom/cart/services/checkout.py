from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.models import Checkout
from cart.models import Cart


class CheckoutService:
    """
    Service layer responsible for managing the checkout lifecycle.

    Enforces checkout state rules, validates cart eligibility,
    and guarantees atomic transitions during checkout operations.
    """

    @staticmethod
    def get_or_create_draft(cart: Cart):
        """
        Retrieve or create a checkout draft for the given cart.

        Only unpaid carts are eligible for checkout creation.
        """
        if cart.status != "unpaid":
            raise ValidationError("Checkout is not allowed for this cart.")

        checkout, _ = Checkout.objects.get_or_create(cart=cart)
        return checkout

    @staticmethod
    @transaction.atomic
    def update_checkout(cart: Cart, data: dict):
        """
        Update the checkout draft associated with the cart.

        Prevents modifications if the cart is no longer unpaid.
        """
        if cart.status != "unpaid":
            raise ValidationError("Checkout can no longer be modified.")

        checkout, _ = Checkout.objects.update_or_create(
            cart=cart,
            defaults=data
        )
        return checkout

    @staticmethod
    @transaction.atomic
    def confirm_checkout(cart: Cart):
        """
        Confirm the checkout and lock the associated cart.

        Validates required checkout fields and transitions the cart
        into a locked state, preventing further modifications.
        """
        
        if cart.status != "unpaid":
            raise ValidationError("Cart is already locked.")

        if not hasattr(cart, "checkout"):
            raise ValidationError("Checkout does not exist.")

        checkout = cart.checkout

        if not checkout.shipping_address:
            raise ValidationError("Shipping address is required.")

        if not checkout.payment_method:
            raise ValidationError("Payment method is required.")

        if not checkout.billing_address:
            raise ValidationError("Billing address is required.")

        cart.status = "pending"
        cart.save(update_fields=["status"])

        return checkout
