from django.contrib import admin
from .models import Vendor, CustomUser, BankAccount, AuthSession
from accounts.services.user_service import create_user, update_user

# Register your models here.
admin.site.register(Vendor)
admin.site.register(BankAccount)
# admin.site.register(AuthSession)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
        "created_at",
    )
    search_fields = ("email", "first_name", "last_name")

    ordering = ("-created_at",)