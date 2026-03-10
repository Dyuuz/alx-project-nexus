from django.contrib import admin
from .models import Vendor, CustomUser, BankAccount, AuthSession


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_active", "created_at")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    list_select_related = True     # JOIN everything (all FK/OneToOne)
    list_per_page = 25
    readonly_fields = ("id", "created_at", "updated_at", "last_login", "version")
    raw_id_fields = ()

    # Limit fields shown on change page — exclude heavy/unused ones
    fields = (
        "id", "email", "first_name", "last_name",
        "phone_number", "role", "email_verified",
        "is_active", "is_staff", "version",
        "created_at", "updated_at", "last_login",
    )


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("business_name", "get_email", "review_status", "activation_status", "created_at")
    search_fields = ("business_name", "user__email")
    ordering = ("-created_at",)
    list_select_related = ("user",)  # avoids N+1 on user__email and JOINs only user
    list_per_page = 25
    raw_id_fields = ("user",)  # prevents loading ALL users into a dropdown
    # replace FK dropdowns on change pages

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = "Email"


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "bank_name", "number", "status")
    search_fields = ("name", "bank_name", "vendor__user__email")
    ordering = ("-created_at",)
    list_select_related = ("vendor", "vendor__user")  # avoids N+1 chain
    list_per_page = 25
    raw_id_fields = ("vendor",)