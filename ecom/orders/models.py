from django.db import models
import uuid
from payment.models import Payment

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )
    payment_status = models.CharField(max_length=10, default="pending")
    status = models.CharField(max_length=8, default="hold")
    date = models.DateTimeField(auto_now_add=True)