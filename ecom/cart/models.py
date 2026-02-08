from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from products.models import Product
from decimal import Decimal
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
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "status"],
                condition=models.Q(status="unpaid"),
                name="unique_unpaid_cart_per_customer",
            )
        ]
    
    @property
    def total_amount(self):
        return sum(item.total_amount for item in self.items.all())
    
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    item_quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart"
            )
        ]
        
    def append_quantity(self, quantity: int):
        if self.cart.status != "unpaid":
            raise ValidationError("This cart can no longer be modified.")

        self.item_quantity += quantity
        self.save(update_fields=["item_quantity"])

    @property
    def total_amount(self):
        price = self.product.original_price
        quantity = self.item_quantity

        if self.product.discount_percent:
            discount = Decimal(self.product.discount_percent) / Decimal("100")
            discounted_price = price * (Decimal("1") - discount)
            return discounted_price * quantity

        return price * quantity
    
    def clean(self):
        if self.cart.status != "unpaid":
            raise ValidationError(
                f"You cannot modify items in a cart that is {self.cart.status}."
            )
            
    def save(self, *args, **kwargs):
        self.full_clean()  # forces clean() to run
        super().save(*args, **kwargs)
    
class Checkout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.OneToOneField(
        Cart,
        on_delete=models.CASCADE,
        related_name="checkout"
    )
    shipping_address = models.TextField(blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)