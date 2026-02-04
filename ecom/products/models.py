from django.db import models
from accounts.models import Vendor
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Create your models here.
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to='images/', blank=True)
    slug = models.SlugField(max_length=50, unique=True, db_index=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True) 

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
    slug = models.SlugField(max_length=50, unique=True, db_index=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='category')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor')
    image = models.ImageField(upload_to='images/', blank=True)
    public_id = models.CharField(blank=True)
    srcURL = models.URLField(blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
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
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate discount amount if discount percent is set
        if self.name:
            self.name = self.name.title().strip()
        if self.discount_percent != 0:
            self.discount_amount = self.original_price * (self.discount_percent / 100)
        if not self.slug:
            self.slug = self.generated_slug
        super().save(*args, **kwargs)

    @property
    def generated_slug(self):
        baseURL = slugify(self.name)
        product_slug = baseURL
        counter = 1
        while Product.objects.filter(slug=product_slug).exists():
            product_slug = f"{baseURL}-{counter}"
            counter += 1
        return product_slug
