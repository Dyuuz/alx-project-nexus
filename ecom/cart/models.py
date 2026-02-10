from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
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
            ("expired", "Expired"),
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='carts')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unpaid")
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "status"],
                condition=models.Q(status="unpaid"),
                name="unique_unpaid_cart_per_customer",
            )
        ]
        
    def __str__(self):
        return f"Cart - {self.customer.email} - {self.status}"
    
    @property
    def total_amount(self):
        """
        Returns the sum of cartItems associated to a cart
        """
        return sum(item.total_amount for item in self.items.all())
    
    def invalidate(self, reason: str | None = None):
        """
        Marks the cart as expired so it can no longer be used.
        Safe to call multiple times.
        """
        if self.status in ("paid", "expired"):
            return

        self.status = "expired"
        self.save(update_fields=["status"])
    
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    item_quantity = models.PositiveIntegerField(default=1)
    last_activity_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart"
            )
        ]
        
    def __str__(self):
        return f"CartItem - {self.cart.customer.email}"
        
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
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Checkout - {self.cart.customer.email}"