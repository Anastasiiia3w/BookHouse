from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import invalidate_catalog_cache
from .models import Category, Product

@receiver(
    [post_save, post_delete],
    sender=Category,
)
def category_changed(sender, instance, **kwargs):
    invalidate_catalog_cache()

@receiver([post_save, post_delete])
def product_changed(sender, instance, **kwargs):
    invalidate_catalog_cache()