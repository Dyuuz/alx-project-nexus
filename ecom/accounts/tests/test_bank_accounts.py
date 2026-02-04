import pytest
from django.urls import reverse
from rest_framework import status
from accounts.models import BankAccount, Vendor

@pytest.mark.django_db
def test_vendor_can_create_bank_account(api_client, vendor_user):
    """
    Test that a vendor can successfully create a bank account.
    Creating a duplicate bank account should fail.
    1st attempt should succeed with 201 Created.
    2nd attempt with same details should fail with 400 Bad Request.
    """
    api_client.force_authenticate(user=vendor_user.user)

    payload = {
        "number": "0123456789",
        "name": "John Doe",
        "bank_name": "Access Bank",
        "bank_code": "044",
        "subaccount_code": "SUB_123456",
    }

    url = reverse("bank-account-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert BankAccount.objects.filter(vendor=vendor_user).exists()
    
    payload = {
        "number": "0123456789",
        "name": "John Doe",
        "bank_name": "Access Bank",
        "bank_code": "044",
        "subaccount_code": "SUB_123456",
    }

    url = reverse("bank-account-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert BankAccount.objects.filter(vendor=vendor_user).exists()
    
@pytest.mark.django_db
def test_vendor_cannot_create_multiple_bank_accounts(api_client, vendor_user):
    """
    Test that a vendor cannot create more than one bank account.
    """
    # Create an existing bank account
    BankAccount.objects.create(
        vendor=vendor_user,
        number="1111111111",
        name="John Doe",
        bank_name="GTBank",
        subaccount_code="SUB_EXISTING",
    )

    api_client.force_authenticate(user=vendor_user.user)

    payload = {
        "number": "2222222222",
        "name": "John Doe",
        "bank_name": "Zenith Bank",
        "subaccount_code": "SUB_NEW",
    }

    url = reverse("bank-account-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert BankAccount.objects.filter(vendor=vendor_user).count() == 1


@pytest.mark.django_db
def test_vendor_can_retrieve_own_bank_account(api_client, vendor_user):
    """
    Test that a vendor can retrieve their own bank account details.
    """
    bank = BankAccount.objects.create(
        vendor=vendor_user,
        number="3333333333",
        name="John Doe",
        bank_name="UBA",
        subaccount_code="SUB_RETRIEVE",
    )

    api_client.force_authenticate(user=vendor_user.user)

    url = reverse("bank-account-detail", args=[bank.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["bank_name"] == "UBA"


@pytest.mark.django_db
def test_vendor_cannot_access_other_users_bank_account(api_client, normal_user, admin_user):
    """
    Test that a vendor cannot access another user's bank account.
    Should return 404 to hide existence of other users' accounts.
    """
    # Ensure both users are vendors
    normal_user.role = 'vendor'
    normal_user.save()
    vendor_normal = Vendor.objects.create(
        user=normal_user,
        business_name="Test Shop",
        business_address="123 Street"
    )

    admin_user.role = 'vendor'
    admin_user.save()
    vendor_admin = Vendor.objects.create(
        user=admin_user,
        business_name="Admin Shop",
        business_address="Admin Street"
    )

    bank = BankAccount.objects.create(
        vendor=vendor_admin,
        number="4444444444",
        name="Admin User",
        bank_name="First Bank",
        subaccount_code="SUB_ADMIN",
    )

    api_client.force_authenticate(user=normal_user)

    url = reverse("bank-account-detail", args=[bank.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_vendor_can_update_own_bank_account(api_client, vendor_user):
    """
    Test that a vendor can update their own bank account.
    """
    bank = BankAccount.objects.create(
        vendor=vendor_user,
        number="5555555555",
        name="John Doe",
        bank_name="Old Bank",
        subaccount_code="SUB_UPDATE",
    )

    api_client.force_authenticate(user=vendor_user.user)

    url = reverse("bank-account-detail", args=[bank.id])
    response = api_client.patch(url, {"bank_name": "New Bank"}, format='json')

    bank.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert bank.bank_name == "New Bank"
