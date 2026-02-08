from django.contrib import admin
from cart.models import Cart, CartItem, Checkout
from django.contrib import messages
from orders.services.order import OrderService
from django.contrib import admin, messages
from rest_framework.exceptions import ValidationError
from cart.services.checkout import CheckoutService

# Register your models here.
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("id", "customer__email")
    actions = ["create_order_from_cart", "confirm_checkout"]
    
    # def get_readonly_fields(self, request, obj=None):
    #     if obj and obj.status != "unpaid":
    #         return [field.name for field in obj._meta.fields]
    #     return super().get_readonly_fields(request, obj)
    
    # def has_change_permission(self, request, obj=None):
    #     if obj and obj.cart.status != "unpaid":
    #         return False
    #     return super().has_change_permission(request, obj)

    # def has_delete_permission(self, request, obj=None):
    #     if obj and obj.cart.status != "unpaid":
    #         return False
    #     return super().has_delete_permission(request, obj)
    
    @admin.action(description="Confirm checkout")
    def confirm_checkout(modeladmin, request, queryset):
        """
        Confirm checkout for the selected carts.

        Attempts to move each cart into a confirmed state using the checkout
        service. Displays a success or error message per cart in the admin UI.
        """
        for cart in queryset:
            try:
                CheckoutService.confirm_checkout(cart)
                messages.success(
                    request,
                    f"Checkout confirmed for cart {cart.id}."
                )
            except ValidationError as e:
                messages.error(
                    request,
                    f"Failed to confirm checkout for cart {cart.id}: {e.detail[0]}"
                )

    def create_order_from_cart(self, request, queryset):
        """
        Create orders from confirmed carts.

        Only carts in a confirmed (pending) state are processed. Order creation
        and recovery logic is fully handled by the order service, with results
        reported back to the admin interface.
        """
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