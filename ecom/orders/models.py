import uuid
from decimal import Decimal
from django.db import transaction
from django.db import models
from accounts.models import CustomUser
from cart.models import Cart
from products.models import Product


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
    
    payment_reminder_sent = models.BooleanField(default=False)
    final_payment_reminder_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        
    def __str__(self):
        return f"Order - {self.customer.email}"

    @property
    def total_amount(self) -> Decimal:
        """
        Returns the total monetary value of all items in the cart.
        """
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))
    
    @transaction.atomic
    def cancel(self, reason: str):
        """
        Cancel an unpaid order and restore reserved stock.

        This operation is idempotent:
        - Calling it multiple times is safe
        - Paid or already-cancelled orders are ignored
        """

        # Only awaiting payment orders can be cancelled safely
        if self.status != "awaiting_payment":
            return

        # Restore stock for each order item
        for item in self.items.select_for_update():
            Product.objects.filter(id=item.product_id).update(
                stock=models.F("stock") + item.quantity
            )
        
        # Expire the cart (order-bound cart should never be reused)
        self.cart.status = "expired"
        self.cart.save(update_fields=["status"])

        # Transition order state
        self.status = "cancelled"
        self.save(update_fields=["status"])


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
    
    def __str__(self):
        return f"OrderItem - {self.order.customer.email}"
