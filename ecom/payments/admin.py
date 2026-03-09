from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "get_customer", "amount", "provider", "status", "payment_alert", "created_at")
    search_fields = ("order__customer__email", "reference")
    ordering = ("-created_at",)
    list_filter = ("status", "provider")
    list_select_related = ("order__customer",)
    list_per_page = 25
    readonly_fields = ("id", "order", "amount", "provider", "reference", "created_at")
    raw_id_fields = ()

    fields = (
        "id", "order", "amount", "provider",
        "reference", "status", "payment_alert", "created_at",
    )

    def get_customer(self, obj):
        return obj.order.customer.email if obj.order.customer else "—"
    get_customer.short_description = "Customer"