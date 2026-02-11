import pytest
from django.urls import reverse
from rest_framework import status
from products.models import Category, Product
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
def test_category_list_is_public(api_client, admin_user, category):
    url = reverse("category-list")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    print(response.data)
    
    data = response.data["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Electronics"


@pytest.mark.django_db
def test_category_retrieve_is_public(api_client, category):
    url = reverse("category-detail", args=[category.id])

    response = api_client.get(url)

    data = response.data["data"]
    assert response.status_code == status.HTTP_200_OK
    assert data["slug"] == "electronics"


@pytest.mark.django_db
def test_admin_can_update_category(api_client, admin_user, category):
    api_client.force_authenticate(user=admin_user)

    url = reverse("category-detail", args=[category.id])
    payload = {"name": "Updated Electronics"}

    response = api_client.patch(url, payload)

    assert response.status_code == status.HTTP_200_OK
    category.refresh_from_db()
    assert category.name == "Updated Electronics"


@pytest.mark.django_db
def test_non_admin_cannot_delete_category(api_client, normal_user, category):
    api_client.force_authenticate(user=normal_user)

    url = reverse("category-detail", args=[category.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_delete_category(api_client, admin_user, category):
    api_client.force_authenticate(user=admin_user)

    url = reverse("category-detail", args=[category.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Category.objects.count() == 0


# @pytest.mark.django_db
# def test_category_name_must_be_unique():
#     Category.objects.create(
#         name="Books",
#         image=SimpleUploadedFile("a.png", b"1", "image/png"),
#         slug="books",
#     )

#     with pytest.raises(Exception):
#         Category.objects.create(
#             name="Books",
#             image=SimpleUploadedFile("b.png", b"2", "image/png"),
#             slug="books-2",
#         )