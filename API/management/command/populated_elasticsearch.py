from django.core.management.base import BaseCommand
from API.models import Product
from API.documents import ProductDocument

class Command(BaseCommand):
    help = 'Populates Elasticsearch with product data'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        for product in products:
            doc = ProductDocument(
                meta={'id': product.id},
                name=product.name,
                description=product.description,
                price=product.price
            )
            doc.save()
        self.stdout.write(self.style.SUCCESS('Successfully populated Elasticsearch with product data'))
