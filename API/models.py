from django.db import models
from django.utils.timezone import now
from django.utils.timezone import now
from datetime import timedelta
from django.core.cache import cache  # Import Django cache
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
# Create your models here.

class SearchModel(models.Model):
    name = models.CharField(max_length=255)  # Field to search
    description = models.TextField(blank=True, null=True)  # Optional field
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for creation

    def __str__(self):
        return self.name 
    
# leads model
class leadsModel(models.Model):
    image = models.ImageField(upload_to='images/')
    products = models.CharField(max_length=100)
    quantity = models.CharField(max_length=100)
    description = models.TextField()
    company_name = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=20, null=True)
    company_email = models.EmailField(max_length=100)
    country = models.CharField(max_length=100)

#Signup Model
class Signup(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=15)
    phone_no = models.CharField(max_length=20, null=True, blank=True)  # Make nullable
    company_name = models.CharField(max_length=100, default="No Company Name")  # Add default
    business_type = models.CharField(max_length=100, default="Individual")
    company_website = models.CharField(max_length=100, null=True, blank=True)  # Make nullable
    country_name = models.CharField(max_length=100, default="Unknown Country")  # Fixed value
    state = models.CharField(max_length=100, default="Unknown State")  # Add default
    city = models.CharField(max_length=100, default="Unknown City")  
    address = models.CharField(max_length=200, default="No Address Provided")  
    company_services = models.CharField(max_length=100, default="General Services")

    can_view_leads = models.BooleanField(default=False)  # ✅ NEW FIELD

#Lead Access Model
class LeadAccess(models.Model):
    user = models.ForeignKey(Signup, on_delete=models.CASCADE)  
    accessed_at = models.DateTimeField(auto_now_add=True)
    
class Login(models.Model):
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=15)
    
# #product Model
# class Product(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     image = models.ImageField(upload_to='products/')
#     description = models.TextField()
#     category = models.CharField(max_length=255,  default="Uncategorized")

#     def __str__(self):
#         return self.name

# #product type model
# class ProductType(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="types")
#     type_name = models.CharField(max_length=255)
#     type_description = models.TextField()

#     def __str__(self):
#         return self.type_name


#Contact Model
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_no = models.CharField(max_length=20)
    subject = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

#for Quick Enquiry
class QuickEnquiry(models.Model):
    phone_no = models.CharField(max_length=15)
    company_name = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)



#leadsView
class LeadView(models.Model):
    user = models.ForeignKey(Signup, on_delete=models.CASCADE)
    lead = models.ForeignKey(leadsModel, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)


#user Fetch the Leads
class UserFetchedLead(models.Model):
    user = models.ForeignKey(Signup, on_delete=models.CASCADE)
    lead_details = models.JSONField()
    fetched_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.fetched_at}"


#category
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products", null=True, blank=True
    )  # Allows products without a category
    description = models.TextField()
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return self.name

# ✅ Corrected: Automatically Update Redis on Product Add/Edit/Delete
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def update_redis_products(sender, instance, **kwargs):
    
    all_products = list(Product.objects.values())  # Fetch all products
    cache.set("all_products", all_products, timeout=86400)  # Cache for 1 day
    
