from django.contrib import admin
from products.models import Product, Category
from products.services.products import (
    create_product,
    update_product,
    delete_product,
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "get_vendor", "get_category", "original_price",
        "stock", "is_active", "created_at"
    )
    search_fields = ("name", "vendor__business_name", "category__name")
    ordering = ("-created_at",)
    list_per_page = 25
    list_select_related = ("vendor", "category")  # avoids N+1 on vendor/category
    raw_id_fields = ("vendor", "category")        # prevents loading full dropdowns on edit page
    readonly_fields = (
        "id", "slug", "public_id", "srcURL",
        "created_at", "updated_at", "last_activity_at"
    )
    list_filter = ("is_active", "category", "vendor")

    def get_vendor(self, obj):
        return obj.vendor.business_name
    get_vendor.short_description = "Vendor"

    def get_category(self, obj):
        return obj.category.name if obj.category else "—"
    get_category.short_description = "Category"
