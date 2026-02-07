import uuid
from decimal import Decimal
from django.db import models
from accounts.models import CustomUser
from cart.models import Cart


class Order(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("awaiting_payment", "Awaiting Payment"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="orders")
    cart = models.OneToOneField(Cart, on_delete=models.PROTECT, related_name="order")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="created")

    shipping_address = models.TextField()
    billing_address = models.TextField()
    payment_method = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    @property
    def total_amount(self) -> Decimal:
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # snapshot fields
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.PositiveIntegerField(default=0)

    quantity = models.PositiveIntegerField(default=1)

    @property
    def line_total(self) -> Decimal:
        price = self.unit_price
        if self.discount_percent:
            discount = Decimal(self.discount_percent) / Decimal("100")
            price = price * (Decimal("1") - discount)
        return price * Decimal(self.quantity)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "product_id"], name="unique_product_per_order"),
        ]
