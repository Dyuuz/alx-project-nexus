import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_admin_can_create_user(api_client, admin_user):
    """
    Test that an admin user can create a new user.
    """
    api_client.force_authenticate(user=admin_user)

    payload = {
        "email": "new@test.com",
        "password": "securepass123",
        "first_name": "New",
        "last_name": "User",
        "phone_number": "+2348123456789",
        "role": "customer",
    }

    url = reverse("user-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="new@test.com").exists()


@pytest.mark.django_db
def test_non_admin_can_create_user(api_client, normal_user):
    """
    Test that a normal user can create a user if allowed by your API.

    NOTE: Normally, non-admins should not create users unless your business logic
    allows it. Adjust test based on your permission rules.
    """
    api_client.force_authenticate(user=normal_user)

    payload = {
        "email": "fail@test.com",
        "password": "pass123456",
        "first_name": "Fail",
        "last_name": "User",
        "phone_number": "+2348133333333",
    }

    url = reverse("user-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_admin_can_update_user(api_client, admin_user, normal_user):
    """
    Test that an admin can update any user's information.
    """
    api_client.force_authenticate(user=admin_user)

    url = reverse("user-detail", args=[normal_user.id])
    payload = {"first_name": "Updated"}

    response = api_client.patch(url, payload)

    normal_user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert normal_user.first_name == "Updated"
    
    
@pytest.mark.django_db
def test_non_admin_can_update_user(api_client, admin_user, normal_user):
    """
    Test that a non-admin user can update their own information.
    """
    api_client.force_authenticate(user=normal_user)

    url = reverse("user-detail", args=[normal_user.id])
    payload = {"first_name": "Updated"}

    response = api_client.patch(url, payload)

    normal_user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert normal_user.first_name == "Updated"


@pytest.mark.django_db
def test_admin_can_delete_user(api_client, admin_user, normal_user):
    """
    Test that an admin can delete a user.
    """
    api_client.force_authenticate(user=admin_user)

    url = reverse("user-detail", args=[normal_user.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(id=normal_user.id).exists()


@pytest.mark.django_db
def test_non_admin_cannot_delete_other_user(api_client, normal_user, admin_user):
    """
    Test that a non-admin user cannot delete another user.
    """
    api_client.force_authenticate(user=normal_user)

    url = reverse("user-detail", args=[admin_user.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert User.objects.filter(id=admin_user.id).exists()