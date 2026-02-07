from django.contrib import admin
from orders.models import Order, OrderItem

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "created_at")
    readonly_fields = (
        "customer",
        "cart",
        "shipping_address",
        "billing_address",
        "payment_method",
        "created_at",
    )

    def has_add_permission(self, request):
        return False  # Orders are created via service only

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Prevent accidental data loss

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "quantity", "unit_price")
    readonly_fields = ("order", "quantity", "unit_price")

    def has_add_permission(self, request):
        return False  # Order items are created via service only

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Prevent accidental data loss
