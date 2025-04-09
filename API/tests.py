
from django.test import TestCase
from API.models import Product
from API.documents import ProductDocument

class ElasticsearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(name="Onion", description="A root vegetable", price=10.0)
        Product.objects.create(name="Tomato", description="A red fruit", price=15.0)

        for product in Product.objects.all():
            doc = ProductDocument(
                meta={'id': product.id},
                name=product.name,
                description=product.description,
                price=product.price
            )
            doc.save()

    def test_search(self):
        search = ProductDocument.search().query("match", name="Onion")
        results = search.execute()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Onion")
