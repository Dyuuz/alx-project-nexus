import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import Vendor

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@test.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        phone_number="+2348012345678",
        role="admin",
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email="user@test.com",
        password="userpass123",
        first_name="Normal",
        last_name="User",
        phone_number="+2348098765432",
        role="customer",
    )

@pytest.fixture
def vendor_user(normal_user):
    """
    Returns a Vendor instance linked to a CustomUser with role='vendor'.
    """
    normal_user.role = 'vendor'
    normal_user.save()
    vendor = Vendor.objects.create(
        user=normal_user,
        business_name="Test Shop",
        business_address="123 Street"
    )
    return vendor