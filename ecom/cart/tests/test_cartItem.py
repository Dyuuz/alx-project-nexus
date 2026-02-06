import pytest
from rest_framework import status
from django.urls import reverse

from cart.models import Cart, CartItem
from products.models import Product

@pytest.mark.django_db
def test_user_can_add_item_to_cart(api_client, normal_user, product):
    """
    Test that an authenticated user can add a product to their cart.

    Verifies that a cart item is created with the correct quantity
    when a valid product is added.
    """
    api_client.force_authenticate(user=normal_user)

    url = reverse("cart-items-list")
    payload = {
        "product_id": product.id,
        "item_quantity": 2
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert CartItem.objects.count() == 1
    assert CartItem.objects.first().item_quantity == 2


@pytest.mark.django_db
def test_user_can_update_cart_item(api_client, normal_user, product):
    """
    Test that an authenticated user can update the quantity of a cart item.
    """
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    item = CartItem.objects.create(cart=cart, product=product, item_quantity=1)

    url = reverse("cart-items-detail", args=[item.id])
    response = api_client.patch(url, {"item_quantity": 3})

    item.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert item.item_quantity == 3

@pytest.mark.django_db
def test_user_can_remove_cart_item(api_client, normal_user, product):
    """
    Test that an authenticated user can remove an item from their cart.
    """
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    item = CartItem.objects.create(cart=cart, product=product, item_quantity=1)

    url = reverse("cart-items-detail", args=[item.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert CartItem.objects.count() == 0

