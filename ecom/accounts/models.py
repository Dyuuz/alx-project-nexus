from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import BaseUserManager
from django.conf import settings
import uuid, os

class CustomManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    objects = CustomManager()

    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("vendor", "Vendor"),
        ("admin", "Admin"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customer")

    email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]
    
    def clean(self):
        """Normalize user data before saving."""
        if self.first_name:
            self.first_name = self.first_name.title().strip()

        if self.last_name:
            self.last_name = self.last_name.title().strip()

        if self.email:
            self.email = self.email.lower().strip()

        # phone_number is already normalized by PhoneNumberField

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    
class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
    )

    business_name = models.CharField(max_length=100)
    business_address = models.TextField()
    verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business_name} ({self.user.email})"    
    
    def clean(self):
        """
        Normalize vendor business data.
        """

        if self.business_name:
            self.business_name = self.business_name.title().strip()

        if self.business_address:
            self.business_address = self.business_address.strip()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        

class AuthSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="auth_sessions")
    
    # OTP fields
    otp = models.CharField(max_length=8, blank=True, null=True)
    otp_expires = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user} - {self.otp} - {self.otp_expires}"

    def verify_otp(self, request, otp):
        """
        Verify OTP and activate session.
        """
        if self.otp != otp:
            return False, "Invalid OTP"

        if self.otp_expires < timezone.now():
            return False, "OTP expired, request a new code."

        return True, "OTP verified successfully"

class BankAccount(models.Model):
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
   vendor = models.OneToOneField(
       Vendor,
       on_delete=models.CASCADE,
       related_name='bank_details'
   )
   number = models.CharField(max_length=20, unique=True)
   name = models.CharField(max_length=200, help_text="Provide the exact bank account name")
   bank_name = models.CharField(max_length=200)
   bank_code = models.CharField(max_length=20, null=True, blank=True)
   subaccount_code = models.CharField(max_length=100, null=True, blank=False, unique=True)
   verified = models.BooleanField(default=False)
   updated_at = models.DateTimeField(auto_now=True)

   def save(self, *args, **kwargs):
       if self.name:
           self.name = self.name.strip()  # keeps exact casing, removes extra spaces
       super().save(*args, **kwargs)

class BlackListAccessToken(models.Model):
    jti = models.CharField(max_length=255, unique=True)
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.jti
