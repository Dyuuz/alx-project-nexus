import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import Vendor
from products.models import Product, Category

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


@pytest.fixture
def product_vendor_user(db):
    user = User.objects.create_user(
        email="vendor@test.com",
        password="password123",
        role="vendor",
        first_name="Vendor",
        last_name="User",
        phone_number="+2348012345679",
    )
    Vendor.objects.create(
        user=user,
        business_name="Vendor Shop",
        business_address="Lagos",
    )
    return user

@pytest.fixture
def other_vendor_user(db):
    user = User.objects.create_user(
        email="vendor2@test.com",
        password="password123",
        role="vendor",
        first_name="Other",
        last_name="Vendor",
        phone_number="+2348012345680",
    )
    Vendor.objects.create(
        user=user,
        business_name="Other Shop",
        business_address="Abuja",
    )
    return user


@pytest.fixture
def category(db):
    return Category.objects.create(name="Electronics")

@pytest.fixture
def product(category, product_vendor_user):
    return Product.objects.create(
        name="Test Product",
        description="Test product description",
        original_price=5000,
        discount_percent=0,
        category=category,
        stock=1,
        vendor=product_vendor_user.vendor_profile,
    )