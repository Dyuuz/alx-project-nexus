import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import Vendor
from products.models import Product, Category
from core.factories import PaymentFactory

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db, worker_id="master"):
    return User.objects.create_superuser(
        email=f"admin_{worker_id}@test.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        phone_number=f"+2348012{worker_id.replace('gw', '0')}5678",
        email_verified=True,
        role="admin",
    )


@pytest.fixture
def normal_user(db, worker_id="master"):
    return User.objects.create_user(
        email=f"user_{worker_id}@test.com",
        password="userpass123",
        first_name="Normal",
        last_name="User",
        phone_number=f"+2348098{worker_id.replace('gw', '0')}5432",
        email_verified=True,
        role="customer",
    )


@pytest.fixture
def vendor_user(normal_user):
    normal_user.role = 'vendor'
    normal_user.save()
    vendor = Vendor.objects.create(
        user=normal_user,
        business_id=166777217899,
        business_name="Test Shop",
        business_address="123 Street"
    )
    return vendor


@pytest.fixture
def product_vendor_user(db, worker_id="master"):
    user = User.objects.create_user(
        email=f"vendor_{worker_id}@test.com",
        password="password123",
        role="vendor",
        first_name="Vendor",
        last_name="User",
        phone_number=f"+2348012{worker_id.replace('gw', '1')}5679",
    )
    Vendor.objects.create(
        user=user,
        business_id=16677767899,
        business_name="Vendor Shop",
        business_address="Lagos",
    )
    return user


@pytest.fixture
def other_vendor_user(db, worker_id="master"):
    user = User.objects.create_user(
        email=f"vendor2_{worker_id}@test.com",
        password="password123",
        role="vendor",
        first_name="Other",
        last_name="Vendor",
        phone_number=f"+2348012{worker_id.replace('gw', '2')}5680",
    )
    Vendor.objects.create(
        user=user,
        business_id=16677755699,
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


@pytest.fixture
def payment_factory():
    return PaymentFactory


@pytest.fixture
def order_factory():
    return PaymentFactory