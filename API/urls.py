from django.urls import path
from . import views
from .views import (
    dashboard, signup, contact, get_leads, lead_details, is_logged_in,
    send_otp, verify_otp, forgot_password, password_verify_otp, reset_password,
    check_email, ProductSearchView, UserProfileView, LoginView, LogoutView,
    get_all_original_leads, AllProductsAPIView, ProductsByCategoryAPIView,
    unified_search_api, initiate_payment, payment_success, payment_failure,
    leads_api, users_api, categories_api, contacts_api, quick_enquiries_api,
    SuperuserLoginView, searchbar, Logout
)

urlpatterns = [
    # Core Views
    path('', searchbar, name='searchbar'),
    path('api/unified-search/', unified_search_api, name='unified_search'),
    path('dashboard/', dashboard, name='dashboard'),
    path('contact/', contact, name='contact'),

    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('is_logged_in/', is_logged_in, name='is_logged_in'),

    # OTP & Password Recovery
    path('api/send-otp/', send_otp, name='send_otp'),
    path('api/verify-otp/', verify_otp, name='verify_otp'),
    path('check-email/', check_email, name='check-email'),
    path('forgot-password/', forgot_password, name='forgot-password'),
    path('password-verify-otp/', password_verify_otp, name='password-verify-otp'),
    path('reset-password/', reset_password, name='reset-password'),

    # User Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),

    # Lead Management
    path('get_leads/', get_leads, name='get_leads'),
    path('lead-details/<int:lead_id>/', lead_details, name='lead_details'),
    path('get-original-lead/<int:lead_id>/', get_all_original_leads, name='get_original_lead'),

    # Product Search & Listing
    path('api/search/', unified_search_api, name='unified_search_api'),
    path('products/', AllProductsAPIView.as_view(), name='all-products'),
    path('api/products/category/<str:category_name>/', ProductsByCategoryAPIView.as_view(), name='products-by-category'),

    # Payment Integration
    path('api/payment/initiate/', initiate_payment, name='initiate_payment'),
    path('api/payment/success/', payment_success, name='payment_success'),
    path('api/payment/failure/', payment_failure, name='payment_failure'),

    # Admin APIs
    path('leads/', leads_api, name='leads_api'),
    path('users/', users_api, name='users_api'),
    path('categories/', categories_api, name='categories_api'),
    path('contacts/', contacts_api, name='contacts_api'),
    path('quick-enquiries/', quick_enquiries_api, name='quick_enquiries_api'),
    path('superuser-login/', SuperuserLoginView.as_view(), name='superuser_login'),
    path('admin/logout/', Logout.as_view(), name='adminlogout'),
]
