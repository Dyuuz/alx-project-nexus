import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError

from cart.models import Cart, CartItem, Checkout
from orders.services.order import OrderService
from cart.services.checkout import CheckoutService
from orders.models import Order
from payments.models import Payment

from payments.models import Payment
from payments.services.payment import PaymentService
from unittest.mock import patch

@pytest.mark.django_db
def test_customer_can_initiate_payment(api_client, normal_user, product):
    """
    Ensure a customer can initiate payment for an order.

    Verifies that a payment record is created after checkout
    confirmation and order creation, with status set to pending.
    """
    
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    CartItem.objects.create(cart=cart, product=product, item_quantity=1)
    checkout = Checkout.objects.create(cart=cart, shipping_address="Lagos", billing_address="Lagos", payment_method="card")

    # Confirm checkout
    # response = api_client.post(reverse("payments-initiate"), {"cart_id": str(cart.id)}, format="json")
    # or
    CheckoutService.confirm_checkout(cart)
    
    cart.refresh_from_db()
    order = OrderService.create_order_with_cart_recovery(cart)

    url = reverse("payments-initiate")
    response = api_client.post(url, {"order_id": str(order.id), "provider": "internal"}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Payment.objects.filter(order=order).exists()
    payment = Payment.objects.get(order=order)
    assert payment.status == "pending"
    
    
@pytest.mark.django_db
def test_customer_cannot_create_order_above_product_stock(
    api_client, normal_user, product
):
    """
    Ensure order creation fails when requested quantity exceeds stock.

    Verifies that no order or payment is created when stock
    validation fails.
    """
    
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    CartItem.objects.create(cart=cart, product=product, item_quantity=3)
    Checkout.objects.create(
        cart=cart,
        shipping_address="Lagos",
        billing_address="Lagos",
        payment_method="card",
    )

    with pytest.raises(ValidationError):
        OrderService.create_order_with_cart_recovery(cart)

    assert not Order.objects.exists()
    assert not Payment.objects.exists()


@pytest.mark.django_db
def test_confirm_payment_marks_order_paid(api_client, normal_user, product):
    """
    Ensure confirming a payment marks the order and cart as paid.

    Verifies that payment confirmation updates the payment,
    order, and cart states correctly.
    """
    
    api_client.force_authenticate(user=normal_user)

    cart = Cart.objects.create(customer=normal_user)
    CartItem.objects.create(cart=cart, product=product, item_quantity=1)
    Checkout.objects.create(cart=cart, shipping_address="Lagos", billing_address="Lagos", payment_method="card")

    CheckoutService.confirm_checkout(cart)
    
    cart.refresh_from_db()
    order = OrderService.create_order_with_cart_recovery(cart)

    # initiate first
    init_url = reverse("payments-initiate")
    init_resp = api_client.post(init_url, {"order_id": str(order.id), "provider": "internal"}, format="json")
    assert init_resp.status_code == status.HTTP_201_CREATED
    reference = init_resp.data["data"]["reference"]

    confirm_url = reverse("payments-confirm")
    confirm_resp = api_client.post(confirm_url, {"reference": reference}, format="json")
    assert confirm_resp.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    cart.refresh_from_db()

    assert order.status == "paid"
    assert cart.status == "paid"


