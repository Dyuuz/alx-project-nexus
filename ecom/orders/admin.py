from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("id", "product_id", "product_name", "unit_price", "discount_percent", "quantity", "line_total")
    can_delete = False
    show_change_link = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "get_customer", "status", "total_amount", "payment_method", "created_at")
    search_fields = ("customer__email",)
    ordering = ("-created_at",)
    list_filter = ("status", "payment_method")
    list_select_related = ("customer", "cart")
    list_per_page = 25
    readonly_fields = (
        "id", "customer", "cart", "total_amount",
        "payment_reminder_sent", "final_payment_reminder_sent", "created_at",
    )
    raw_id_fields = ("customer", "cart")
    inlines = [OrderItemInline]

    fields = (
        "id", "customer", "cart", "status",
        "shipping_address", "billing_address", "payment_method",
        "total_amount", "payment_reminder_sent", "final_payment_reminder_sent",
        "created_at",
    )

    def get_customer(self, obj):
        return obj.customer.email if obj.customer else "—"
    get_customer.short_description = "Customer"
    
    def has_add_permission(self, request):
        return False  # Orders are created via service only

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Prevent accidental data loss


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "get_customer", "product_name", "unit_price", "discount_percent", "quantity", "line_total")
    search_fields = ("order__customer__email", "product_name")
    ordering = ("-order__created_at",)
    list_select_related = ("order__customer",)
    list_per_page = 25
    readonly_fields = ("id", "product_id", "product_name", "unit_price", "discount_percent", "quantity", "line_total")
    raw_id_fields = ("order",)

    fields = (
        "id", "order", "product_id", "product_name",
        "unit_price", "discount_percent", "quantity", "line_total",
    )

    def get_customer(self, obj):
        return obj.order.customer.email if obj.order.customer else "—"
    get_customer.short_description = "Customer"
    
    def has_add_permission(self, request):
        return False  # Order items are created via service only

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Prevent accidental data loss
