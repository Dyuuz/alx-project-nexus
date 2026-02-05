from django.db import transaction
from products.models import Category


@transaction.atomic
def create_category(data: dict) -> Category:
    return Category.objects.create(**data)


@transaction.atomic
def update_category(category: Category, data: dict) -> Category:
    for field, value in data.items():
        setattr(category, field, value)
    category.save()
    return category


@transaction.atomic
def delete_category(category: Category) -> None:
    category.delete()
