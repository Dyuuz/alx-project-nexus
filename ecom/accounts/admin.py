from django.contrib import admin
from .models import Vendor, CustomUser, BankAccount, AuthSession

# Register your models here.
admin.site.register(Vendor)
admin.site.register(CustomUser)
admin.site.register(BankAccount)
# admin.site.register(AuthSession)