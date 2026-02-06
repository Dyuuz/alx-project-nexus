import pytest
from django.urls import reverse
from rest_framework import status

from cart.models import Cart, Checkout

@pytest.mark.django_db
def test_customer_can_create_checkout(api_client, normal_user, product):
    """
    Test that a customer can initiate checkout when their cart has items.

    Ensures a checkout record is created for the user's active cart.
    """
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    cart.items.create(product=product, item_quantity=1)

    url = reverse("checkout-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert Checkout.objects.filter(cart=cart).exists()


@pytest.mark.django_db
def test_checkout_update_fails_for_empty_cart(api_client, normal_user):
    """
    Test that checkout updates are rejected when the cart is empty.
    """

    api_client.force_authenticate(user=normal_user)

    Cart.objects.create(customer=normal_user)

    url = reverse("checkout-update-draft")
    response = api_client.patch(url, {"shipping_address": "Lagos"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_confirm_checkout_locks_cart(api_client, normal_user, product):
    """
    Test that confirming a checkout locks the cart from further modification.

    Verifies that the cart status is updated to prevent additional changes.
    """
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    cart.items.create(product=product, item_quantity=1)

    Checkout.objects.create(
        cart=cart,
        shipping_address="Lagos",
        payment_method="card"
    )

    url = reverse("checkout-confirm")
    response = api_client.post(url)

    cart.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert cart.status == "pending"


@pytest.mark.django_db
def test_vendor_cannot_access_checkout(api_client, vendor_user):
    """
    Test that vendors are forbidden from accessing checkout endpoints.
    """
    api_client.force_authenticate(user=vendor_user.user)

    url = reverse("checkout-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
