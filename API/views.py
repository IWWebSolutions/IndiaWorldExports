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
# from django.utils.decorators import method_decorator
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
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

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
    
def search_products(request):
    query = request.GET.get('q', '')
    search = ProductDocument.search().query("multi_match", query=query, fields=['name', 'description'])
    results = search.execute()
    data = [{'id': hit.meta.id, 'name': hit.name, 'description': hit.description} for hit in results]
    return JsonResponse(data, safe=False)


from django.db.models.functions import Lower
@api_view(['GET'])
def unified_search_api(request):
    query = request.GET.get('q', '').strip().lower()
    search_type = request.GET.get('type', 'product')

    if not query:
        return Response({'error': 'Query parameter is required'}, status=400)

    if search_type == 'product':
        products = Product.objects.filter(name__icontains=query)
        if products.exists():
            results = ProductSerializer(products, many=True, context={'request': request}).data
            return Response({'results': results})
        else:
            return Response({'message': 'Product not available'})

    elif search_type == 'lead':
        leads = leadsModel.objects.annotate(
            lower_products=Lower('products')
        ).filter(lower_products__icontains=query)
        if leads.exists():
            results = LeadsSerializer(leads, many=True, context={'request': request}).data
            return Response({'results': results})
        else:
            return Response({'message': 'No leads found for this product'})

    return Response({'error': 'Invalid search type'}, status=400)


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





# @method_decorator(csrf_exempt, name='dispatch')

class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({'msg': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = Signup.objects.filter(email=email).first()

        if not user or not check_password(password, user.password):
            return Response({'msg': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if not user:
            return Response({'msg': 'Incorrect username '}, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({'msg': 'Incorrect Password'}, status=status.HTTP_400_BAD_REQUEST)


        # Generate access and refresh tokens
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
    
@api_view(['GET'])
def lead_details(request, lead_id):
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)
    
    # Fetch the lead and the user
    lead = get_object_or_404(leadsModel, id=lead_id)
    user = get_object_or_404(Signup, id=request.user.id)

    # Check if the user has permission to view leads
    if not user.can_view_leads:
        return Response({"error": "You don't have permission to view leads."}, status=403)

    # Check weekly access limit
    one_week_ago = now() - timedelta(weeks=1)
    views_this_week = LeadAccess.objects.filter(user=user, accessed_at__gte=one_week_ago).count()

    if views_this_week >= 2:
        return Response({"error": "Lead limit reached. You can access more leads next week."}, status=403)

    # Log access
    LeadAccess.objects.create(user=user)

    # Serialize and return lead details
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

redis_client = redis.Redis(host='api.indiaworldexports.in', port=6379, db=1, decode_responses=True)


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


class ProductsByCategoryAPIView(APIView):
    def get(self, request, category_name):
        cache_key = f"products_{category_name.lower()}"  # Unique cache key per category
        cached_data = cache.get(cache_key)

        if cached_data:
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
        return Response(serialized_data)


class AllProductsAPIView(APIView):
    def get(self):
        cache_key = "all_products"  # Unique cache key for all products
        cached_data = cache.get(cache_key)

        if cached_data:
            
            return Response(cached_data)

        # Fetch all products from DB if not in cache
        products = Product.objects.all()

        if not products.exists():
            
            return Response({"error": "No products available"}, status=404)

        serialized_data = ProductSerializer(products, many=True).data

        # Store in Redis cache for 30 minutes
        cache.set(cache_key, serialized_data, timeout=1800)  
        

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






#for custom dashboard


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import leadsModel, Signup, Product, Category, Contact, QuickEnquiry
from .serializers import  SignupSerializers, ProductSerializer, CategorySerializer, ContactSerializer, QuickEnquirySerializer, LeadsCreateSerializer

# Lead APIs
@api_view(['GET', 'POST'])
def leads_api(request):
    if request.method == 'GET':
        leads = leadsModel.objects.all()
        serializer = LeadsCreateSerializer(leads, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = LeadsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User APIs
@api_view(['GET'])
def users_api(request):
    users = Signup.objects.all()
    serializer = SignupSerializers(users, many=True)
    return Response(serializer.data)

# Product APIs
class AllProductsAPIView(APIView):
    def get(self, request, *args, **kwargs):  # ✅ Correct parameters
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    def post(self, request, *args, **kwargs):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400)


# Category APIs
@api_view(['GET'])
def categories_api(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)

# Contact APIs
@api_view(['GET'])
def contacts_api(request):
    contacts = Contact.objects.all()
    serializer = ContactSerializer(contacts, many=True)
    return Response(serializer.data)

# Quick Enquiry APIs
@api_view(['GET'])
def quick_enquiries_api(request):
    enquiries = QuickEnquiry.objects.all()
    serializer = QuickEnquirySerializer(enquiries, many=True)
    return Response(serializer.data)



#Custom dashboard 




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

class SuperuserLoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username) 
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(username=user.username, password=password)
        if user is not None:
            if not user.is_superuser:
                return Response({"error": "Access denied: superusers only"}, status=status.HTTP_403_FORBIDDEN)

            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "username": user.username,
                "email": user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
#for admin logout
        
from rest_framework.permissions import AllowAny

class Logout(APIView):
    permission_classes = [AllowAny]  # Allow even if access token is expired

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
