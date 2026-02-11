from django.db import models
from accounts.models import Vendor
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import F
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
import uuid

# Create your models here.
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, blank=False, null=False)
    image = CloudinaryField('image')
    slug = models.SlugField(max_length=50, unique=True, db_index=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) 
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.title()
        if not self.slug:
            self.slug = self.create_slug_for_category
        super().save(*args, **kwargs)

    @property
    def create_slug_for_category(self):
        baseURL = slugify(self.name)
        slug = baseURL
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{baseURL}-{counter}"
            counter += 1
        return slug
    

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=50, unique=True, db_index=True, blank=True,null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    image = CloudinaryField('image')
    public_id = models.CharField(blank=True)
    srcURL = models.URLField(blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    initial_stock = models.PositiveIntegerField(
        default=0,
        help_text="Stock quantity when the product was first created"
    )
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text="Alert when stock falls below this quantity",
    )
    critical_stock_alert_sent = models.BooleanField(default=False)
    low_stock_alert_sent = models.BooleanField(default=False)

    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    discount_percent = models.PositiveIntegerField(
                    validators=[MinValueValidator(0), MaxValueValidator(70)],
                    default=0, help_text="Discount percentage (0-70).", null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name="stock_cannot_be_negative",
            )
        ]
        
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.title().strip()
        if not self.slug:
            self.slug = self.generated_slug
        super().save(*args, **kwargs)
        
    
    def reconcile_stock_alerts(self):
        """
        Reset stock alert flags when stock is safely above thresholds.
        """
        if self.stock > self.low_stock_threshold:
            self.low_stock_alert_sent = False
            self.critical_stock_alert_sent = False
            
    def update_stock(self, new_stock: int):
        if new_stock == self.stock:
            return

        now = timezone.now()

        Product.objects.filter(pk=self.pk).update(
            stock=new_stock,
            last_activity_at=now,
            low_stock_alert_sent=(
                False if new_stock > self.low_stock_threshold else F("low_stock_alert_sent")
            ),
            critical_stock_alert_sent=(
                False if new_stock > self.low_stock_threshold else F("critical_stock_alert_sent")
            ),
        )

        # keep in-memory instance in sync
        self.stock = new_stock
        self.last_activity_at = now

    @property
    def generated_slug(self):
        baseURL = slugify(self.name)
        product_slug = baseURL
        counter = 1
        while Product.objects.filter(slug=product_slug).exists():
            product_slug = f"{baseURL}-{counter}"
            counter += 1
        return product_slug
