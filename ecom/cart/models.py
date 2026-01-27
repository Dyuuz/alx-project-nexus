from django.db import models
from accounts.models import CustomUser
from products.models import Product
import uuid

# Create your models here.
class Cart(models.Model):
    STATUS_CHOICES = [
            ("unpaid", "Unpaid"),
            ("pending", "Pending"),
            ("paid", "Paid"),
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unpaid")
    
    @property
    def total_amount(self):
        return sum(item.total_amount for item in self.items.all())
    
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    item_quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_amount(self):
        if self.product.discount_percent != 0:
            discount_amount = self.product.original_price * (self.product.discount_percent / 100)
            total_amount = discount_amount * self.item_quantity
        else:
            total_amount = self.product.original_price * self.item_quantity
        return total_amount
    
class Checkout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)