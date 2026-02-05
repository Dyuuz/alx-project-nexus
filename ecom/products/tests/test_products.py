import pytest
from django.urls import reverse
from rest_framework import status
from products.models import Category, Product

@pytest.mark.django_db
def test_vendor_can_create_product(api_client, product_vendor_user, category):
    api_client.force_authenticate(user=product_vendor_user)

    url = reverse("product-list")
    payload = {
        "name": "iphone 15",
        "description": "Latest Apple smartphone",
        "category": category.id,
        "original_price": "1000.00",
        "discount_percent": 10,
        "stock": 5,
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == 201

    product = Product.objects.get()
    assert product.name == "Iphone 15"
    assert product.discount_amount == 100
    assert product.vendor == product_vendor_user.vendor_profile


@pytest.mark.django_db
def test_vendor_cannot_spoof_vendor_on_create(
    api_client, product_vendor_user, other_vendor_user, category
):
    api_client.force_authenticate(user=product_vendor_user)

    url = reverse("product-list")
    payload = {
        "name": "Laptop",
        "description": "Latest Apple laptop",
        "vendor": other_vendor_user.vendor_profile.id,
        "category": category.id,
        "original_price": "2000.00",
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == 201

    product = Product.objects.get(name="Laptop")
    assert product.vendor == product_vendor_user.vendor_profile


@pytest.mark.django_db
def test_vendor_can_update_own_product(api_client, product_vendor_user, category):
    product = Product.objects.create(
        name="Tablet",
        description="Latest Android tablet",
        vendor=product_vendor_user.vendor_profile,
        category=category,
        original_price=500,
    )

    api_client.force_authenticate(user=product_vendor_user)

    url = reverse("product-detail", args=[product.id])
    response = api_client.patch(
        url,
        {"discount_percent": 20},
        format="json",
    )

    assert response.status_code == 200

    product.refresh_from_db()
    assert product.discount_amount == 100


@pytest.mark.django_db
def test_vendor_cannot_update_other_vendor_product(
    api_client, product_vendor_user, other_vendor_user, category
):
    product = Product.objects.create(
        name="Camera",
        vendor=other_vendor_user.vendor_profile,
        description="Latest camera",
        category=category,
        original_price=800,
    )

    api_client.force_authenticate(user=product_vendor_user)

    url = reverse("product-detail", args=[product.id])
    response = api_client.patch(url, {"stock": 10}, format="json")

    assert response.status_code == 404


@pytest.mark.django_db
def test_admin_can_update_any_product(
    api_client, admin_user, product_vendor_user, other_vendor_user, category
):
    product = Product.objects.create(
        name="Monitor",
        vendor=other_vendor_user.vendor_profile,
        description="Latest Apple monitor",
        category=category,
        original_price=1200,
    )

    api_client.force_authenticate(user=admin_user)

    url = reverse("product-detail", args=[product.id])
    response = api_client.patch(
        url,
        {"discount_percent": 25},
        format="json",
    )

    assert response.status_code == 200

    product.refresh_from_db()
    assert product.discount_amount == 300


@pytest.mark.django_db
def test_customer_cannot_create_product(api_client, normal_user, category):
    api_client.force_authenticate(user=normal_user)
    
    payload = {
        "name": "iphone 15",
        "description": "Latest Apple smartphone",
        "category": category.id,
        "original_price": "1000.00",
        "discount_percent": 10,
        "stock": 5,
    }
    
    url = reverse("product-list")
    response = api_client.post(
        url,
        payload,
        format="json",
    )

    assert response.status_code == 403