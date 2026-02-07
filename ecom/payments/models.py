import uuid
from decimal import Decimal
from django.db import models
from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    provider = models.CharField(max_length=50, default="internal")  # e.g. paystack/stripe/internal
    reference = models.CharField(max_length=120, unique=True)       # external or generated reference
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)