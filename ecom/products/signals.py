from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from products.models import Product

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_product_cache(sender, **kwargs):
    cache.delete("all_active_products")