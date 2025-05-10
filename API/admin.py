from django.contrib import admin
from .models import SearchModel, Product, leadsModel, Signup, Login, Contact, LeadAccess, QuickEnquiry, UserFetchedLead
from .models import Product, Category
# Register your models here.
@admin.register(SearchModel)
class SearchAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')  # Fields to display in admin
    search_fields = ('name', 'description')  # Enable search in admin
    
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description', 'price', 'created_at')  # Fields
#     search_fields = ('name', 'description')  # Enable search in admin

@admin.register(leadsModel)
class leadsAdmin(admin.ModelAdmin):
    list_display = ('image','products', 'quantity', 'company_name', 'phone_no', 'company_email','country')  # Fields
    search_fields = ('products', 'company_name', 'country')


@admin.register(LeadAccess)
class LeadAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'accessed_at')
    search_fields = ('user__username',)  # Search by username
    list_filter = ('accessed_at',)

    
# @admin.register(Signup)
# class SignupAdmin(admin.ModelAdmin):
#     list_display=('id', 'name', 'email', 'password', 'phone_no', 'company_name', 'business_type', 'company_website', 'country_name', 'state', 'city', 'address', 'company_services')
  
@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'can_view_leads')
    list_editable = ('can_view_leads',)


@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display=('email', 'password')
    
@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display=('name', 'email', 'phone_no', 'subject' , 'message')

@admin.register(QuickEnquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('id','phone_no', 'company_name', 'date')

@admin.register(UserFetchedLead)
class FetchedLeads(admin.ModelAdmin):
    list_display = ('id', 'user', 'lead_details','fetched_at')
    


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "description")
    search_fields = ("name", "category__name")
    list_filter = ("category",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

