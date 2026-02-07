from django.contrib import admin
from cart.models import Cart, CartItem, Checkout
from cart.models import Cart
from orders.services.order import OrderService
from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError

# Register your models here.
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("id", "customer__email")
    actions = ["create_order_from_cart"]

    def create_order_from_cart(self, request, queryset):
        for cart in queryset:
            # Enforce lifecycle rule
            if cart.status != "pending":
                self.message_user(
                    request,
                    f"Cart {cart.id} is not confirmed (status={cart.status}).",
                    level=messages.WARNING,
                )
                continue

            try:
                # Enforce ALL business rules via service
                order = OrderService.create_order_with_cart_recovery(cart)

                self.message_user(
                    request,
                    f"Order {order.id} created successfully for cart {cart.id}.",
                    level=messages.SUCCESS,
                )

            except ValidationError as exc:
                # Cart recovery already handled in service
                self.message_user(
                    request,
                    f"Failed to create order for cart {cart.id}: {exc}",
                    level=messages.ERROR,
                )

            except Exception as exc:
                # Catch unexpected errors (DB, integrity, etc.)
                self.message_user(
                    request,
                    f"Unexpected error for cart {cart.id}: {exc}",
                    level=messages.ERROR,
                )

    create_order_from_cart.short_description = "Create order from confirmed cart"

admin.site.register(CartItem)
admin.site.register(Checkout)