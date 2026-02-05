from django.contrib import admin
from products.models import Product
from products.services.products import (
    create_product,
    update_product,
    delete_product,
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vendor",
        "original_price",
        "discount_percent",
        "discount_amount",
        "stock",
        "created_at"
    )
    list_filter = ("vendor", "category")
    search_fields = ("name", "vendor__business_name")

    def save_model(self, request, obj, form, change):
        """
        Force Django admin to use the ProductService
        instead of calling obj.save() directly.
        """
        data = form.cleaned_data

        if change:
            update_product(obj.id, **data)
        else:
            create_product(**data)

    def delete_model(self, request, obj):
        delete_product(obj)
