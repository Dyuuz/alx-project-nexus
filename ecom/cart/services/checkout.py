from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from cart.models import Checkout
from cart.models import Cart
from cart.services.cart_guards import assert_cart_is_modifiable


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
        assert_cart_is_modifiable(cart)

        checkout, _ = Checkout.objects.get_or_create(cart=cart)
        return checkout

    @staticmethod
    @transaction.atomic
    def update_checkout(cart: Cart, data: dict):
        """
        Update the checkout draft associated with the cart.

        Prevents modifications if the cart is no longer unpaid.
        """
        assert_cart_is_modifiable(cart)
        
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
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
        
        assert_cart_is_modifiable(cart)
        
        try:
            checkout = cart.checkout
            
        except ObjectDoesNotExist:
            raise ValidationError("Checkout does not exist.")

        checkout = cart.checkout

        if not checkout.shipping_address:
            raise ValidationError("Shipping address is required.")

        if not checkout.payment_method:
            raise ValidationError("Payment method is required.")

        if not checkout.billing_address:
            raise ValidationError("Billing address is required.")
        
        if not cart.items.exists():
            raise ValidationError("Cannot create an order from an empty cart.")
        
        errors = []

        for item in cart.items.select_related("product"):
            product = item.product
            if item.item_quantity > product.stock:
                errors.append(
                    {
                        "product_id": str(product.id),
                        "product_name": product.name,
                        "requested_quantity": item.item_quantity,
                        "available_stock": product.stock,
                    }
                )

        if errors:
            raise ValidationError(
                {
                    "code": "INSUFFICIENT_STOCK",
                    "message": "Some items exceed available stock.",
                    "items": errors,
                }
            )

        cart.status = "pending"
        cart.save(update_fields=["status"])

        return checkout
