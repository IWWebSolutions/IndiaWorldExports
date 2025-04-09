from django.urls import path
from . import views
from django.urls import path
from .views import ProductSearchView, signup,  get_leads, dashboard, contact, UserProfileView, LoginView, LogoutView, send_otp, verify_otp, forgot_password, password_verify_otp, reset_password, check_email,lead_details, is_logged_in, get_all_original_leads, AllProductsAPIView, ProductsByCategoryAPIView


urlpatterns = [
    
    path('dashboard/', dashboard, name='dashboard'),
    path('', views.searchbar, name='searchbar'),
    path('login/', LoginView.as_view(), name='login' ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', signup, name='signup'),
    path('api/search/', ProductSearchView.as_view(), name='product_search'),
    # path("send-otp/", send_otp_view, name="send-otp"),
    path('get_leads/', get_leads, name='get_leads'),
    path('lead-details/<int:lead_id>/', lead_details, name='lead_details'),
    path('is_logged_in', is_logged_in, name='is_logged_in'),
    path('contact/', contact, name='contact'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path("api/send-otp/", send_otp, name="send_otp"),
    path("api/verify-otp/", verify_otp, name="verify_otp"),
    path("check-email/", check_email, name="check-email"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("password-verify-otp/", password_verify_otp, name="password-verify-otp"),
    path("reset-password/", reset_password, name="reset-password"),
    path("get-original-lead/<int:lead_id>/", get_all_original_leads, name="get_original_lead"),
    # path('api/products/<str:name>/', product_detail, name='product_detail'),
    path("products/", AllProductsAPIView.as_view(), name="all-products"),
    path("api/products/category/<str:category_name>/", ProductsByCategoryAPIView.as_view(), name="products-by-category"),
    path('api/payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('api/payment/success/', views.payment_success, name='payment_success'),
    path('api/payment/failure/', views.payment_failure, name='payment_failure'),
    
]


