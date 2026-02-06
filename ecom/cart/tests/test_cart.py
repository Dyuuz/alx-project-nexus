import pytest
from rest_framework import status
from django.urls import reverse

from cart.models import Cart

@pytest.mark.django_db
def test_user_can_create_cart(api_client, normal_user):
    """
    Test that an authenticated user can retrieve their cart.

    If no active cart exists, the system should automatically
    create an unpaid cart for the user and return it.
    """
    
    api_client.force_authenticate(user=normal_user)

    url = reverse("cart-detail", args=["me"])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert Cart.objects.filter(customer=normal_user).exists()
