import pytest
from django.urls import reverse
from rest_framework import status

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
def test_recover_from_insufficient_stock_and_create_order_successfully(
    api_client, normal_user, product
):
    """
    Validates recovery from an insufficient stock failure during order creation.

    This test ensures the system can safely recover when an order attempt fails
    due to stock constraints, without leaving the cart in a broken or locked state.

    Flow covered:
    - A product has limited stock.
    - The user attempts to create an order with a quantity greater than available stock.
    - Order creation is rejected with a validation error.
    - The cart is automatically reverted to an editable (unpaid) state.
    - The user corrects the cart quantity to a valid value.
    - Checkout is re-confirmed.
    - Order creation succeeds on retry.

    This guarantees:
    - Atomic order creation (no partial orders).
    - Proper cart state rollback on failure.
    - Idempotent and recoverable checkout → order flow.
    - Users can safely fix cart issues and retry without data corruption.
    """


    api_client.force_authenticate(user=normal_user)

    product.stock = 1
    product.save()
    
    cart = Cart.objects.create(customer=normal_user)
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        item_quantity=2,  # exceeds stock
    )

    Checkout.objects.create(
        cart=cart,
        shipping_address="Lagos",
        billing_address="Lagos",
        payment_method="card",
    )
    
    CheckoutService.confirm_checkout(cart)

    create_order_url = reverse("orders-create-from-checkout")

    #  Act 1: attempt order creation (should fail) 
    response = api_client.post(create_order_url, {})
    print(response.data)

    #  Assert 1: order fails and cart is reverted 
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Insufficient stock" in str(response.data)

    cart.refresh_from_db()
    assert cart.status == "unpaid"

    #  Act 2: user updates cart item to valid quantity 
    cart_item.item_quantity = 1
    cart_item.save()

    # re-confirm checkout (cart must be pending again)
    CheckoutService.confirm_checkout(cart)

    #  Act 3: retry order creation 
    retry_response = api_client.post(create_order_url, {})

    #  Assert 2: order is successfully created 
    assert retry_response.status_code == status.HTTP_201_CREATED

    order = Order.objects.get(cart=cart)
    assert order.items.count() == 1
    assert order.items.first().quantity == 1


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
