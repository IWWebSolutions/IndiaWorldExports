from elasticsearch_dsl import Document, Text, Float

class ProductDocument(Document):
    name = Text()
    description = Text()
    price = Float()

    class Index:
        # Name of the Elasticsearch index
        name = 'products'
