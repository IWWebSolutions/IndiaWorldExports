import random
import requests
import json
import redis
from .models import SearchModel,Signup, leadsModel, LeadAccess, QuickEnquiry, UserFetchedLead, Product, Category
from rest_framework.response import Response
from .serializers import SearchSerializer, SignupSerializers, LoginSerializers, LeadsSerializer, ContactSerializer,ResetPasswordSerializer, ProductSerializer,PaymentInitiateSerializer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from django.views import View
from .models import Product
from django.shortcuts import redirect, get_object_or_404
from .documents import ProductDocument
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils.timezone import now
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .payu_helper import generate_hash, verify_hash
import uuid

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Restrict access to logged-in users

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user  # Get the authenticated user
    user_data = Signup.objects.filter(id=user.id).values().first()

    if not user_data:
        return Response({"msg": "User not found"}, status=404)

    return Response({"msg": "Dashboard Data", "user": user_data}, status=200)
  
#for search the products
@api_view(['GET'])
def searchbar(request):
    query = request.GET.get('query', '')
    results = []

    if query:
        results = SearchModel.objects.filter(name__icontains=query)
    serialized_results = SearchSerializer(results, many=True)
    return Response(serialized_results.data)

#for product search views
class ProductSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        if query:
            products = Product.objects.filter(name__icontains=query)
        else:
            products = Product.objects.all()
        data = [{'id': product.id, 'name': product.name} for product in products]
        return JsonResponse(data, safe=False)

# @api_view(['GET'])
# def universal_search(request):
#     query = request.GET.get('query', '')
#     search_type = request.GET.get('type', '')  # Get search type (product, supplier, lead)

#     if not query:
#         return Response({"message": "No search query provided."}, status=status.HTTP_400_BAD_REQUEST)

#     if search_type == 'product':
#         # Search for products
#         results = Product.objects.filter(name__icontains=query)
#         serialized_results = ProductSerializer(results, many=True)
#     elif search_type == 'supplier':
#         # Search for suppliers (using Signup model for suppliers)
#         results = Signup.objects.filter(company_name__icontains=query)
#         serialized_results = SignupSerializers(results, many=True)
#     elif search_type == 'lead':
#         # Search for leads
#         results = leadsModel.objects.filter(products__icontains=query)
#         serialized_results = LeadsSerializer(results, many=True)
#     else:
#         return Response({"message": "Invalid search type."}, status=status.HTTP_400_BAD_REQUEST)

#     return Response(serialized_results.data)


from django.db.models.functions import Lower
@api_view(['GET'])
def unified_search_api(request):
    query = request.GET.get('q', '').strip().lower()
    search_type = request.GET.get('type', 'product')
    print("there are search type", search_type)

    if not query:
        return Response({'error': 'Query parameter is required'}, status=400)

    results = []

    if search_type == 'product':
        products = Product.objects.filter(name__icontains=query)
        results = ProductSerializer(products, many=True, context={'request': request}).data

    elif search_type == 'supplier':
        suppliers = Signup.objects.filter(company_services__icontains=query)
        results = SignupSerializers(suppliers, many=True).data

   
    elif search_type == 'lead':
        leads = leadsModel.objects.annotate(
            lower_products=Lower('products')
        ).filter(lower_products__icontains=query.strip())
        results = LeadsSerializer(leads, many=True, context={'request': request}).data
        print("Lead search query:", query)
        print("Lead results:", leads.count())
     
    return Response({'results': results})  # ✅ Wrap results in dictionary


#for signup 
@api_view(['POST'])  # Make sure this decorator allows POST method
def signup(request):
    if request.method == 'POST':
        data = request.data  # Use request.data for DRF
        serializer = SignupSerializers(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Your account has been created'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({'error': 'Invalid method'}, status=405)  # In case any other method like GET is used


class LoginView(APIView):
    def post(self, request):
        print("Received Data:", request.data)  # Debugging line

        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({'msg': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = Signup.objects.filter(email=email).first()
        if not user:
            print("User not found!")  # Debugging
            return Response({'msg': 'Incorrect username '}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            print("Password does not match!")  # Debugging
            return Response({'msg': 'Incorrect Password'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'msg': 'Login successful',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'name': user.name,
            }
        }, status=status.HTTP_200_OK)



class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # This gets the logged-in user based on the token
        return Response({
            'name': user.name,
            'email': user.email,
            'phone': user.phone,  # Include all required fields
            # Add other signup form fields
            'company_name': user.company_name,
            'compnay_website': user.compnay_website,
            'country_name': user.country_name,
            'state': user.state,
            'city': user.city,
            'address': user.address,
            'company_services': user.company_services,
            
        })
#for otp verifications

FAST2SMS_API_KEY = "fVPsHo0GJiLXRARwbIj7AuXnlT9hqTr6H5t1mO9wF4A5LqJVqdGxZqxmPBv4"

@api_view(['POST'])
def send_otp(request):
    phone_no = request.data.get('phone_no')
    company_name = request.data.get('company_name')

    if not phone_no or not company_name:
        return Response({"error": "Phone number and company name are required."}, status=400)

    # Generate a 6-digit OTP
    import random
    otp = random.randint(100000, 999999)

    # Send OTP via Fast2SMS API
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "route": "otp",
        "numbers": phone_no,
        "message": f"Your OTP is {otp}. Do not share OTP with anyone. It is valid for 5 minutes",
        "flash": "0"
    }

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        # Save phone number and company name to database
        enquiry = QuickEnquiry.objects.create(phone_no=phone_no, company_name=company_name)
        return Response({"success": "OTP sent successfully!", "otp": otp})  # In production, do NOT return OTP
    else:
        return Response({"error": "Failed to send OTP"}, status=500)


@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        phone_no = request.POST.get("phone_no")
        entered_otp = request.POST.get("otp")

        if not phone_no or not entered_otp:
            return JsonResponse({"error": "Phone number and OTP are required"}, status=400)

        saved_otp = cache.get(f"otp_{phone_no}")

        if saved_otp and str(saved_otp) == entered_otp:
            cache.delete(f"otp_{phone_no}")  # Clear OTP after verification
            
            # Create or update user record in Signup model
            user, created = Signup.objects.get_or_create(phone_no=phone_no)
            user.company_name = request.POST.get("company_name", user.company_name)
            user.save()

            return JsonResponse({"message": "OTP verified successfully", "user_id": user.id})
        else:
            return JsonResponse({"error": "Invalid OTP"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)







@api_view(['GET'])
def get_leads(request):
    query = request.GET.get('q', '')
    leads = leadsModel.objects.filter(products__icontains=query) if query else leadsModel.objects.all()
    serializer = LeadsSerializer(leads, many=True)

    if request.user.is_authenticated:
        # Fetch the logged-in user from `Signup` model
        user = get_object_or_404(Signup, id=request.user.id)

        # Check weekly access limit
        one_week_ago = now() - timedelta(weeks=1)
        views_this_week = LeadAccess.objects.filter(user=user, accessed_at__gte=one_week_ago).count()

        if views_this_week >= 2:
            return Response({"error": "Lead limit reached. You can access more leads next week."}, status=403)

        LeadAccess.objects.create(user=user)  # Log access
        return Response(serializer.data)  # Full details for logged-in users

    return Response(serializer.data)


@api_view(['GET'])
def get_all_original_leads(request, lead_id):
    try:
        lead = leadsModel.objects.get(id=lead_id)  # Fetch a single lead

        original_lead = {
            "id": lead.id,
            "product": lead.products,
            "quantity": lead.quantity,
            "company_name": lead.company_name,
            "company_email": lead.company_email,
            "phone_number": lead.phone_no,
            "country_name": lead.country,
        }

        return JsonResponse(original_lead)  # Return a single object

    except leadsModel.DoesNotExist:
        return JsonResponse({"error": "Lead not found"}, status=404)

# @api_view(['GET'])
# def lead_details(request, lead_id):
#     if not request.user.is_authenticated:
#         return Response({"error": "Authentication required"}, status=401)

#     user = get_object_or_404(Signup, id=request.user.id)

#     # Remove this check or implement it properly in your model
#     # if not user.can_view_leads:
#     #     return Response({"error": "You don't have permission to view leads."}, status=403)

#     one_week_ago = now() - timedelta(weeks=1)
#     views_this_week = LeadAccess.objects.filter(user=user, accessed_at__gte=one_week_ago).count()

#     if views_this_week >= 2:
#         return Response({"error": "Lead limit reached. Try again next week."}, status=403)

#     LeadAccess.objects.create(user=user)
#     lead = get_object_or_404(leadsModel, id=lead_id)
#     serializer = LeadsSerializer(lead, context={'request': request})
#     return Response(serializer.data)

@api_view(['GET'])
def lead_details(request, lead_id):
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    user = get_object_or_404(Signup, id=request.user.id)

    if not user.can_view_leads:
        return Response({"error": "You don't have permission to view leads."}, status=403)

    # Rest of your view code...

    one_week_ago = now() - timedelta(weeks=1)
    views_this_week = LeadAccess.objects.filter(user=user, accessed_at__gte=one_week_ago).count()

    if views_this_week >= 2:
        return Response({"error": "Lead limit reached. Try again next week."}, status=403)

    LeadAccess.objects.create(user=user)
    lead = get_object_or_404(leadsModel, id=lead_id)
    serializer = LeadsSerializer(lead, context={'request': request})
    return Response(serializer.data)




@api_view(['GET'])
def is_logged_in(request):
    return Response({"is_authenticated": request.user.is_authenticated})


#for previous leads
@api_view(['POST'])
def fetch_lead(request):
    if request.user.is_authenticated:
        lead_data = request.data
        UserFetchedLead.objects.create(user=request.user, lead_details=lead_data)
        return Response({"message": "Lead stored successfully"})
    return Response({"error": "Unauthorized"}, status=401)

#for get the previous leads for the user 
@api_view(['GET'])
def previous_leads(request):
    if request.user.is_authenticated:
        leads = UserFetchedLead.objects.filter(user=request.user).order_by('-fetched_at')
        return Response({"leads": [lead.lead_details for lead in leads]})
    return Response({"error": "Unauthorized"}, status=401)




@csrf_exempt
@api_view(['POST'])  # Make sure this decorator allows POST method
def contact(request):
    if request.method == 'POST':
        data = request.data  # Use request.data for DRF
        serializer = ContactSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'Your account has been created'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return JsonResponse({'error': 'Invalid method'}, status=405)





#for logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({'msg': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist the token so it can't be reused

            return Response({'msg': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'msg': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)









#for quick enquiry 
FAST2SMS_API_KEY = "your_fast2sms_api_key_here"

@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        phone_no = request.POST.get("phone_no")
        company_name = request.POST.get("company_name")

        if not phone_no:
            return JsonResponse({"error": "Phone number is required"}, status=400)

        otp = random.randint(100000, 999999)  # Generate 6-digit OTP
        cache.set(f"otp_{phone_no}", otp, timeout=300)  # Store OTP for 5 minutes

        # Send OTP via Fast2SMS
        payload = {
            "authorization": FAST2SMS_API_KEY,
            "message": f"Your OTP is {otp}. Please do not share it.",
            "numbers": phone_no,
            "route": "otp",
            "sender_id": "SMSIND"
        }
        
        response = requests.post("https://www.fast2sms.com/dev/bulkV2", data=payload)

        if response.status_code == 200:
            return JsonResponse({"message": "OTP sent successfully"})
        else:
            return JsonResponse({"error": "Failed to send OTP"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)



@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        phone_no = request.POST.get("phone_no")
        entered_otp = request.POST.get("otp")

        if not phone_no or not entered_otp:
            return JsonResponse({"error": "Phone number and OTP are required"}, status=400)

        saved_otp = cache.get(f"otp_{phone_no}")

        if saved_otp and str(saved_otp) == entered_otp:
            cache.delete(f"otp_{phone_no}")  # Clear OTP after verification
            
            # Create or update user record in Signup model
            user, created = Signup.objects.get_or_create(phone_no=phone_no)
            user.company_name = request.POST.get("company_name", user.company_name)
            user.save()

            return JsonResponse({"message": "OTP verified successfully", "user_id": user.id})
        else:
            return JsonResponse({"error": "Invalid OTP"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)




#redis_client = redis.Redis(host='host.docker.internal', port=6379, db=1, decode_responses=True)

redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)


@csrf_exempt
def check_email(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")

        if Signup.objects.filter(email=email).exists():
            return JsonResponse({"exists": True})
        else:
            return JsonResponse({"exists": False})

    return JsonResponse({"message": "Use POST to check email."}, status=405)  # 405 = Method Not Allowed


@csrf_exempt
def forgot_password(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if Signup.objects.filter(email=email).exists():
                otp = random.randint(100000, 999999)  # Generate 6-digit OTP
                print(f"Generated OTP: {otp}")

                redis_client.setex(f"otp:{email}", 300, otp)  
                send_mail(
                    "Your Password Reset OTP",
                    f"Your OTP for password reset is: {otp}",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )

                return JsonResponse({"sent": True, "message": "OTP sent to email!"})
            else:
                return JsonResponse({"sent": False, "message": "Email not found!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"message": "Use POST to request OTP."}, status=405)


@csrf_exempt
def password_verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            user_otp = data.get("otp")
            stored_otp = redis_client.get(f"otp:{email}")

            if stored_otp and stored_otp == str(user_otp):  # Ensure comparison is between strings
                return JsonResponse({"verified": True, "message": "OTP Verified!"})
            else:
                return JsonResponse({"verified": False, "message": "Invalid OTP"}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"message": "Use POST to verify OTP."}, status=405)


@api_view(["PATCH"])
def reset_password(request):

    try:
        email = request.data.get("email")
        user = Signup.objects.get(email=email)

        serializer = ResetPasswordSerializer(user, data=request.data, partial=True)  # Allow partial update
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Password reset successful!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Signup.DoesNotExist:
        return Response({"success": False, "message": "User not found!"}, status=status.HTTP_404_NOT_FOUND)


# import base64

# def encrypt_data(value):
#     return base64.b64encode(value.encode()).decode()

# def decrypt_data(value):
#     return base64.b64decode(value.encode()).decode()

# @api_view(['GET'])
# def lead_details(request, lead_id):
#     if not request.user.is_authenticated:
#         return Response({"error": "Authentication required"}, status=401)

#     user = get_object_or_404(Signup, id=request.user.id)
#     one_week_ago = now() - timedelta(weeks=1)
#     views_this_week = LeadAccess.objects.filter(user=user, accessed_at__gte=one_week_ago).count()

#     if views_this_week >= 2:
#         return Response({"error": "Lead limit reached. You can access more leads next week."}, status=403)

#     LeadAccess.objects.create(user=user)

#     lead = get_object_or_404(leadsModel, id=lead_id)
#     serializer = LeadsSerializer(lead)

#     # ✅ Encrypt sensitive data before sending
#     data = serializer.data
#     data["phone_no"] = encrypt_data(data["phone_no"])
#     data["company_name"] = encrypt_data(data["company_name"])
#     data["company_email"] = encrypt_data(data["company_email"])

#     return Response(data)



# # Get all products
# @api_view(['GET'])
# def product_list(request):
#     products = Product.objects.all()
#     serializer = ProductSerializer(products, many=True)
#     return Response(serializer.data)

# # Get product details
# @api_view(['GET'])
# def product_detail(request, name):
#     product = Product.objects.filter(name=name).first()
#     if product:
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)
#     return Response({'error': 'Product not found'}, status=404)


# @api_view(['GET'])
# def product_detail(request, name):
#     product = Product.objects.filter(name=name).prefetch_related("types").first()
#     if product:
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)
#     return Response({'error': 'Product not found'}, status=404)


# class ProductsByCategoryAPIView(APIView):
#     def get(self, request, category_name):
#         cache_key = f"products_{category_name.lower()}"  # Unique cache key per category
#         cached_data = cache.get(cache_key)

#         if cached_data:
#             print(f"Serving '{category_name}' from Redis Cache ✅")
#             return Response(cached_data)

#         # Fetch category and products
#         category = Category.objects.filter(name__iexact=category_name).first()  # Returns None if not found
#         if not category:
#             return Response({"error": "Category not found"}, status=404)

#         products = Product.objects.filter(category=category)

#         if not products.exists():
#             return Response({"error": f"No products found for '{category_name}'"}, status=404)

#         serialized_data = ProductSerializer(products, many=True).data
#         cache.set(cache_key, serialized_data, timeout=3600)  # Cache for 1 hour

#         print(f"Stored '{category_name}' in Redis Cache ✅")
#         return Response(serialized_data)



class ProductsByCategoryAPIView(APIView):
    def get(self, request, category_name):
        cache_key = f"products_{category_name.lower()}"  # Unique cache key per category
        cached_data = cache.get(cache_key)

        if cached_data:
            print(f"Serving '{category_name}' from Redis Cache ✅")
            return Response(cached_data)

        # Fetch category and products
        category = Category.objects.filter(name__iexact=category_name).first()
        if not category:
            return Response({"error": "Category not found"}, status=404)

        products = Product.objects.filter(category=category)
        if not products.exists():
            return Response({"error": f"No products found for '{category_name}'"}, status=404)

        # ✅ Pass `context={'request': request}`
        serialized_data = ProductSerializer(products, many=True, context={'request': request}).data
        cache.set(cache_key, serialized_data, timeout=3600)  # Cache for 1 hour

        print(f"Stored '{category_name}' in Redis Cache ✅")
        return Response(serialized_data)


class AllProductsAPIView(APIView):
    def get(self, request):
        cache_key = "all_products"  # Unique cache key for all products
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Serving all products from Redis Cache")
            return Response(cached_data)

        # Fetch all products from DB if not in cache
        products = Product.objects.all()

        if not products.exists():
            print("No products found in DB")
            return Response({"error": "No products available"}, status=404)

        serialized_data = ProductSerializer(products, many=True).data

        # Store in Redis cache for 30 minutes
        cache.set(cache_key, serialized_data, timeout=1800)  
        print("Stored all products in Redis Cache")

        return Response(serialized_data)


# for Payment Gatway of PayU


@api_view(['POST'])
def initiate_payment(request):
    serializer = PaymentInitiateSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        txnid = uuid.uuid4().hex[:20]
        payload = {
            'key': settings.PAYU_MERCHANT_KEY,
            'txnid': txnid,
            'amount': str(data['amount']),
            'productinfo': "Sample Product",
            'firstname': data['firstname'],
            'email': data['email'],
            'phone': data['phone'],
            'surl': request.build_absolute_uri('/api/payment/success/'),
            'furl': request.build_absolute_uri('/api/payment/failure/'),
            'service_provider': 'payu_paisa'
        }
        payload['hash'] = generate_hash(payload, settings.PAYU_MERCHANT_SALT)
        payload['action'] = settings.PAYU_BASE_URL
        return Response(payload)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def payment_success(request):
    # Optional: Verify the hash here using verify_hash() method
    is_valid = verify_hash(request.data, settings.PAYU_MERCHANT_SALT)
    if is_valid:
        # Save transaction details here
        return Response({'message': 'Payment verified and successful', 'data': request.data})
    return Response({'error': 'Hash mismatch'}, status=400)

@api_view(['POST'])
def payment_failure(request):
    return Response({'message': 'Payment failed', 'data': request.data})
