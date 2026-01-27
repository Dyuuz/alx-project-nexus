from django.db import models
from django.conf import settings
from accounts.models import CustomUser
from cart.models import CartItem 
import uuid

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    method = models.CharField(max_length=8, default="card")
    status = models.CharField(max_length=10, default="pending")
    reference = models.CharField(max_length=30, unique=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)