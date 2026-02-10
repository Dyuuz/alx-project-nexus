from django.contrib import admin
from products.models import Product, Category
from products.services.products import (
    create_product,
    update_product,
    delete_product,
)

admin.site.register(Category)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vendor",
        "original_price",
        "discount_percent",
        "discount_amount",
        "initial_stock",
        "stock",
        "last_activity_at"
    )
    list_filter = ("vendor", "category")
    search_fields = ("name", "vendor__business_name")
    readonly_fields = ("last_activity_at","initial_stock")

    def save_model(self, request, obj, form, change):
        data = form.cleaned_data

        if change:
            product = update_product(obj.id, **data)
        else:
            product = create_product(**data)
            obj.pk = product.pk 

        obj.refresh_from_db()

    def delete_model(self, request, obj):
        delete_product(obj)
        
    def save_related(self, request, form, formsets, change):
        """
        Prevent Django admin from trying to re-save M2M relationships
        when persistence is handled in the service layer.
        """
        pass
