import pytest
from django.urls import reverse
from rest_framework import status
from accounts.models import BankAccount

@pytest.mark.django_db
def test_vendor_can_create_bank_account(api_client, normal_user):
    """
    Test that a vendor can successfully create a bank account.
    """
    api_client.force_authenticate(user=normal_user)

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
    assert BankAccount.objects.filter(vendor=normal_user).exists()


@pytest.mark.django_db
def test_vendor_cannot_create_multiple_bank_accounts(api_client, normal_user):
    """
    Test that a vendor cannot create more than one bank account.
    """
    BankAccount.objects.create(
        vendor=normal_user,
        number="1111111111",
        name="John Doe",
        bank_name="GTBank",
        subaccount_code="SUB_EXISTING",
    )

    api_client.force_authenticate(user=normal_user)

    payload = {
        "number": "2222222222",
        "name": "John Doe",
        "bank_name": "Zenith Bank",
        "subaccount_code": "SUB_NEW",
    }

    url = reverse("bank-account-list")
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert BankAccount.objects.filter(vendor=normal_user).count() == 1


@pytest.mark.django_db
def test_vendor_can_retrieve_own_bank_account(api_client, normal_user):
    """
    Test that a vendor can retrieve their own bank account details.
    """
    bank = BankAccount.objects.create(
        vendor=normal_user,
        number="3333333333",
        name="John Doe",
        bank_name="UBA",
        subaccount_code="SUB_RETRIEVE",
    )

    api_client.force_authenticate(user=normal_user)

    url = reverse("bank-account-detail", args=[bank.id])
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["bank_name"] == "UBA"


@pytest.mark.django_db
def test_vendor_cannot_access_other_users_bank_account(
    api_client, normal_user, admin_user
):
    """
    Test that a vendor cannot access another user's bank account.
    Should return 404 to hide existence of other users' accounts.
    """
    bank = BankAccount.objects.create(
        vendor=admin_user,
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
def test_vendor_can_update_own_bank_account(api_client, normal_user):
    """
    Test that a vendor can update their own bank account.
    """
    bank = BankAccount.objects.create(
        vendor=normal_user,
        number="5555555555",
        name="John Doe",
        bank_name="Old Bank",
        subaccount_code="SUB_UPDATE",
    )

    api_client.force_authenticate(user=normal_user)

    url = reverse("bank-account-detail", args=[bank.id])
    response = api_client.patch(url, {"bank_name": "New Bank"}, format='json')
    print(response.data)

    bank.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert bank.bank_name == "New Bank"


@pytest.mark.django_db
def test_admin_can_delete_vendor_bank_account(api_client, admin_user, normal_user):
    """
    Test that an admin user can delete a vendor's bank account.
    """
    bank = BankAccount.objects.create(
        vendor=normal_user,
        number="6666666666",
        name="John Doe",
        bank_name="Delete Bank",
        subaccount_code="SUB_DELETE",
    )

    api_client.force_authenticate(user=admin_user)

    url = reverse("bank-account-detail", args=[bank.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not BankAccount.objects.filter(id=bank.id).exists()
