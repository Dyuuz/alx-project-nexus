from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
import uuid, os

# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("vendor", "Vendor"),
        ("admin", "Admin"),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="customer")

    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

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
        related_name="vendor_profile"
    )

    business_name = models.CharField(max_length=100)
    business_address = models.TextField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
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