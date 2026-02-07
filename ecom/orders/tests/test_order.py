import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem, Checkout
from cart.services.checkout import CheckoutService
from cart.services import cartItem, cart
from orders.models import Order
from products.models import Product


@pytest.mark.django_db
def test_customer_can_create_order_from_confirmed_checkout(api_client, normal_user, product):
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    CartItem.objects.create(cart=cart, product=product, item_quantity=1)

    Checkout.objects.create(
        cart=cart,
        shipping_address="Lagos",
        billing_address="Lagos",
        payment_method="card",
    )
    CheckoutService.confirm_checkout(cart)
     
    url = reverse("orders-create-from-checkout")
    response = api_client.post(url, {})

    assert response.status_code == status.HTTP_201_CREATED
    assert Order.objects.filter(cart=cart).exists()
    order = Order.objects.get(cart=cart)
    assert order.items.count() == 1


@pytest.mark.django_db
def test_checkout_fails_if_cart_quantity_exceeds_stock(api_client, normal_user, product):
    api_client.force_authenticate(user=normal_user)

    product.stock = 1
    product.save()

    cart = Cart.objects.create(customer=normal_user)
    CartItem.objects.create(
        cart=cart,
        product=product,
        item_quantity=2,
    )

    Checkout.objects.create(
        cart=cart,
        shipping_address="Lagos",
        billing_address="Lagos",
        payment_method="card",
    )

    with pytest.raises(ValidationError) as exc:
        CheckoutService.confirm_checkout(cart)

    cart.refresh_from_db()
    assert cart.status == "unpaid"
    assert exc.value.detail["code"] == "INSUFFICIENT_STOCK"



@pytest.mark.django_db
def test_cannot_create_order_without_confirmed_cart(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    Cart.objects.create(customer=normal_user, status="unpaid")

    url = reverse("orders-create-from-checkout")
    response = api_client.post(url, {})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_vendor_cannot_create_order(api_client, other_vendor_user):
    api_client.force_authenticate(user=other_vendor_user)

    url = reverse("orders-create-from-checkout")
    response = api_client.post(url, {})

    assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)
