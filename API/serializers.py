from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import (
    Product, SearchModel, Signup, Login, leadsModel,
    Contact, QuickEnquiry, Category
)

# --- Search ---
class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchModel
        fields = ['id', 'name', 'description', 'created_at']


# --- Signup ---
class SignupSerializers(serializers.ModelSerializer):
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return Signup.objects.create(**validated_data)

    class Meta:
        model = Signup
        fields = [
            'id', 'name', 'email', 'password', 'phone_no',
            'company_name', 'business_type', 'company_website',
            'country_name', 'state', 'city', 'address', 'company_services'
        ]


# --- Login ---
class LoginSerializers(serializers.ModelSerializer):
    class Meta:
        model = Login
        fields = ['id', 'email', 'password']


# --- Contact ---
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone_no', 'subject', 'message']


# --- Quick Enquiry ---
class QuickEnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickEnquiry
        fields = ['phone_no', 'company_name']


# --- Reset Password ---
class ResetPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Signup
        fields = ['email', 'new_password']

    def update(self, instance, validated_data):
        instance.password = make_password(validated_data['new_password'])
        instance.save()
        return instance


# --- Product ---
class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'image_url']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


# --- Leads (Masked + Full View) ---
class LeadsSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    company_email = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()

    class Meta:
        model = leadsModel
        fields = ['id', 'products', 'quantity', 'company_name', 'phone_no', 'company_email', 'country']

    def mask_data(self, data, mask_length=5):
        if data and len(data) > mask_length:
            start = (len(data) - mask_length) // 2
            end = start + mask_length
            return data[:start] + '*' * mask_length + data[end:]
        return "********"

    def mask_phone(self, phone):
        return phone[:4] + '*******' if phone and len(phone) > 4 else "********"

    def get_company_name(self, obj):
        request = self.context.get('request')
        return obj.company_name if request and request.user.is_authenticated else self.mask_data(obj.company_name)

    def get_company_email(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.company_email
        name, domain = obj.company_email.split('@')
        return f"{self.mask_data(name)}@{domain}"

    def get_phone_no(self, obj):
        request = self.context.get('request')
        return obj.phone_no if request and request.user.is_authenticated else self.mask_phone(obj.phone_no)


class LeadsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = leadsModel
        fields = [
            'id', 'image', 'products', 'quantity',
            'description', 'company_name', 'phone_no', 'company_email', 'country'
        ]


# --- Payment ---
class PaymentInitiateSerializer(serializers.Serializer):
    firstname = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


# --- Category ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
