from django.contrib import admin
from cart.models import Cart, CartItem, Checkout
from django.contrib import messages
from orders.services.order import OrderService
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from cart.services.checkout import CheckoutService
from cart.forms.checkout import CheckoutAdminForm
from cart.services.cart_guards import assert_cart_is_modifiable
from cart.services.cartItem import CartItemService

# Register your models here.
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "created_at", "last_activity_at")
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
    
    def confirm_checkout(self, request, queryset):
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
                
            except ValidationError as exc:
                # Cart recovery already handled in service
                self.message_user(
                    request,
                    f"Failed to confirm checkout for cart {cart.id}: {exc}",
                    level=messages.ERROR,
                )

            except Exception as exc:
                # Catch unexpected errors (DB, integrity, etc.)
                self.message_user(
                    request,
                    f"Failed to confirm checkout for cart {cart.id}: {exc}",
                    level=messages.ERROR,
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
            if cart.status == "paid":
                self.message_user(
                    request,
                    f"Cart {cart.id} was skipped because it has already been paid.",
                    level=messages.WARNING,
                )
                continue

            if cart.status == "expired":
                self.message_user(
                    request,
                    f"Cart {cart.id} was skipped because it is no longer active.",
                    level=messages.WARNING,
                )
                continue

            if cart.status == "unpaid":
                self.message_user(
                    request,
                    f"Cart {cart.id} was skipped because it has not been confirmed for checkout.",
                    level=messages.INFO,
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

    confirm_checkout.short_description = "Confirm checkout"
    create_order_from_cart.short_description = "Create order from confirmed cart"
    

@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    readonly_fields = ("cart",)
    form = CheckoutAdminForm

    def save_model(self, request, obj, form, change):
        try:
            CheckoutService.update_checkout(
                cart=obj.cart,
                data=form.cleaned_data,
            )
        except ValidationError as e:
            self.message_user(request, str(e), level="ERROR")
            return None

    def response_change(self, request, obj):
        if "_confirm_checkout" in request.POST:
            try:
                CheckoutService.confirm_checkout(obj.cart)
            except ValidationError as e:
                self.message_user(request, str(e), level="ERROR")
                return None

        return super().response_change(request, obj)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "item_quantity")
    readonly_fields = ("cart", "product")
    
    def save_model(self, request, obj, form, change):
        try:
            assert_cart_is_modifiable(obj.cart)
            
            if change:
                quantity = form.cleaned_data.get("item_quantity")
                
                CartItemService.update_item(obj.cart, obj.id, quantity=quantity)
            
        except ValidationError as e:
            self.message_user(request, str(e), level="ERROR")
            return None
