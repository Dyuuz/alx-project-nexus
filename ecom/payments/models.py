from django.db import models
from accounts.models import CustomUser
import uuid

# Create your models here.
class BankAccount(models.Model):
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
   vendor = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='bank_details')
   number = models.CharField(max_length=20, unique=True)
   name = models.CharField(max_length=200, help_text="Provide the exact bank account name")
   bank_name = models.CharField(max_length=200)
   bank_code = models.CharField(max_length=20, null=True, blank=True)
   subaccount_code = models.CharField(max_length=100, null=True, blank=False, unique=True)
   verified = models.BooleanField(default=False)
   updated_at = models.DateTimeField(auto_now=True)

   def save(self, *args, **kwargs):
        if self.name:
           self.name = self.name.strip()
        super().save(*args, **kwargs)