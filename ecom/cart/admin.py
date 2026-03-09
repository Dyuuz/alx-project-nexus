from django.contrib import admin
from cart.models import Cart, CartItem, Checkout
from django.contrib import messages
from orders.services.order import OrderService
from django.core.exceptions import ValidationError
from cart.services.checkout import CheckoutService
from cart.forms.checkout import CheckoutAdminForm
from cart.services.cart_guards import assert_cart_is_modifiable
from cart.services.cartItem import CartItemService


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("id", "product", "item_quantity", "total_amount", "created_at", "updated_at")
    can_delete = False
    show_change_link = True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "get_customer", "status", "total_amount", "last_activity_at", "created_at")
    list_filter = ("status",)
    search_fields = ("id", "customer__email")
    ordering = ("-created_at",)
    list_select_related = ("customer",)
    list_per_page = 25
    readonly_fields = ("id", "total_amount", "created_at", "updated_at", "last_activity_at")
    raw_id_fields = ("customer",)
    inlines = [CartItemInline]
    actions = ["create_order_from_cart", "confirm_checkout"]

    fields = (
        "id", "customer", "status",
        "total_amount", "last_activity_at",
        "created_at", "updated_at",
    )

    def get_customer(self, obj):
        return obj.customer.email if obj.customer else "—"
    get_customer.short_description = "Customer"

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
                self.message_user(
                    request,
                    f"Failed to confirm checkout for cart {cart.id}: {exc}",
                    level=messages.ERROR,
                )

            except Exception as exc:
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
                    level=messages.WARNING,
                )
                continue

            try:
                order = OrderService.create_order_with_cart_recovery(cart)
                self.message_user(
                    request,
                    f"Order {order.id} created successfully for cart {cart.id}.",
                    level=messages.SUCCESS,
                )

            except ValidationError as exc:
                self.message_user(
                    request,
                    f"Failed to create order for cart {cart.id}: {exc}",
                    level=messages.ERROR,
                )

            except Exception as exc:
                self.message_user(
                    request,
                    f"Unexpected error for cart {cart.id}: {exc}",
                    level=messages.ERROR,
                )

    confirm_checkout.short_description = "Confirm checkout"
    create_order_from_cart.short_description = "Create order from confirmed cart"


@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    """
    Admin interface for managing checkouts.

    Enforces checkout business rules by delegating all mutations
    to the CheckoutService instead of saving directly.
    """
    list_display = ("id", "get_customer", "payment_method", "created_at", "updated_at")
    search_fields = ("cart__customer__email",)
    ordering = ("-created_at",)
    list_select_related = ("cart__customer",)
    list_per_page = 25
    readonly_fields = ("id", "cart", "created_at", "updated_at")
    raw_id_fields = ()
    form = CheckoutAdminForm

    fields = (
        "id", "cart", "shipping_address",
        "billing_address", "payment_method",
        "created_at", "updated_at",
    )

    def get_customer(self, obj):
        return obj.cart.customer.email if obj.cart.customer else "—"
    get_customer.short_description = "Customer"

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
    """
    Updates cart items via the CartItemService.

    Prevents direct writes and blocks modifications
    when the cart is no longer editable.
    """
    list_display = ("id", "get_customer", "product", "item_quantity", "total_amount", "created_at")
    search_fields = ("cart__customer__email", "product__name")
    ordering = ("-created_at",)
    list_select_related = ("cart__customer", "product")
    list_per_page = 25
    readonly_fields = ("id", "total_amount", "created_at", "updated_at", "last_activity_at")
    raw_id_fields = ("cart", "product")

    fields = (
        "id", "cart", "product",
        "item_quantity", "total_amount",
        "last_activity_at", "created_at", "updated_at",
    )

    def get_customer(self, obj):
        return obj.cart.customer.email if obj.cart.customer else "—"
    get_customer.short_description = "Customer"

    def save_model(self, request, obj, form, change):
        """
        Creates or updates cart items through the CartItemService.

        Prevents direct writes and blocks modifications
        when the cart is no longer editable.
        """
        try:
            assert_cart_is_modifiable(obj.cart)

            quantity = form.cleaned_data.get("item_quantity")

            if change:
                CartItemService.update_item(
                    cart=obj.cart,
                    cart_item_id=obj.id,
                    quantity=quantity,
                )
            else:
                CartItemService.add_item(
                    cart=obj.cart,
                    product_id=obj.product.id,
                    quantity=quantity,
                )

            return

        except ValidationError as e:
            self.message_user(request, str(e), level="ERROR")
            raise