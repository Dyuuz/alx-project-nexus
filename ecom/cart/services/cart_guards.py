from rest_framework.exceptions import ValidationError

NON_MODIFIABLE_CART_STATES = {
    "paid": "This cart has already been paid and cannot be modified.",
    "expired": "This cart is no longer active.",
    "pending": "This cart is currently in checkout and cannot be modified.",
}

def assert_cart_is_modifiable(cart, *, allow_admin_override=False):
    """
    Ensures the cart can be modified.

    By default, only unpaid carts are modifiable.
    Admin override must be explicitly allowed.
    """
    message = NON_MODIFIABLE_CART_STATES.get(cart.status)

    if message:
        if allow_admin_override:
            return
        raise ValidationError(message)
