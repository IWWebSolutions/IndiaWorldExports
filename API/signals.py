from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from API.models import Product
from API.serializers import ProductSerializer

def update_product_cache():
    """ Fetch all products from DB and store in Redis cache """
    products = Product.objects.all()
    serialized_data = ProductSerializer(products, many=True).data
    cache.set("all_products", serialized_data, timeout=1800)  # 30 minutes cache

@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_and_update_cache(sender, instance, **kwargs):
    """ Clears and updates Redis cache when a Product is added/updated/deleted """
    print("🔄 Product updated! Refreshing Redis cache...")
    cache.delete("all_products")  # Clear old cache
    update_product_cache()  # Store updated data in cache
