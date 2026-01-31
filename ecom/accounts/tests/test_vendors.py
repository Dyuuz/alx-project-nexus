import pytest
from django.urls import reverse
from rest_framework import status
from accounts.models import Vendor

@pytest.mark.django_db
def test_user_can_create_vendor_profile(api_client, normal_user):
    """
    Test that an authenticated user can create their vendor profile.
    """
    api_client.force_authenticate(user=normal_user)

    payload = {
        "business_name": "Test Business",
        "business_address": "Lagos, Nigeria",
    }

    url = reverse("vendor-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert Vendor.objects.filter(user=normal_user).exists()


@pytest.mark.django_db
def test_user_cannot_access_other_vendor(api_client, normal_user, admin_user):
    """
    Test that a user cannot access another user's vendor profile.
    The API returns 404 to avoid leaking existence.
    """
    vendor = Vendor.objects.create(
        user=admin_user,
        business_name="Admin Biz",
        business_address="Abuja",
    )

    api_client.force_authenticate(user=normal_user)

    url = reverse("vendor-detail", args=[vendor.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_vendor_can_update_own_profile(api_client, normal_user):
    """
    Test that a vendor can update their own business profile.
    """
    vendor = Vendor.objects.create(
        user=normal_user,
        business_name="Old Name",
        business_address="Lagos",
    )

    api_client.force_authenticate(user=normal_user)

    url = reverse("vendor-detail", args=[vendor.id])
    response = api_client.patch(url, {"business_name": "New Name"})

    vendor.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert vendor.business_name == "New Name"


@pytest.mark.django_db
def test_vendor_cannot_delete_own_profile(api_client, normal_user):
    """
    Test that a vendor cannot delete their own profile.
    """
    vendor = Vendor.objects.create(
        user=normal_user,
        business_name="Delete Me",
        business_address="Ibadan",
    )

    api_client.force_authenticate(user=normal_user)

    url = reverse("vendor-detail", args=[vendor.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Vendor.objects.filter(id=vendor.id).exists()
    

@pytest.mark.django_db
def test_admin_can_delete_user_profile(api_client, normal_user, admin_user):
    """
    Test that an admin can delete another user's vendor profile.
    """
    vendor = Vendor.objects.create(
        user=normal_user,
        business_name="Delete Me",
        business_address="Ibadan",
    )

    api_client.force_authenticate(user=admin_user)

    url = reverse("vendor-detail", args=[vendor.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Vendor.objects.filter(id=vendor.id).exists()
