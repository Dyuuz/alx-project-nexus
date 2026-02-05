from django.db import transaction
from products.models import Product


@transaction.atomic
def create_product(**data):
    product = Product(**data)
    _apply_pricing(product)
    product.save()
    return product


@transaction.atomic
def update_product(product_id, **data):
    product = Product.objects.get(id=product_id)
    data.pop("vendor", None)

    for key, value in data.items():
        setattr(product, key, value)

    _apply_pricing(product)
    product.save()
    return product


@transaction.atomic
def delete_product(product):
    product.delete()


def _apply_pricing(product):
    if product.discount_percent:
        product.discount_amount = (
            product.original_price * product.discount_percent / 100
        )
    else:
        product.discount_amount = 0
