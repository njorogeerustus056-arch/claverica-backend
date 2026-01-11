# accounts/urls.py - UPDATED
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    IndexView,
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    VerifyEmailOTPView,
    ResendVerificationOTPView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    CurrentAccountView
)

app_name = 'accounts'

urlpatterns = [
    # Health check
    path('', IndexView.as_view(), name='index'),
    
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Email verification with OTP
    path('verify-email/', VerifyEmailOTPView.as_view(), name='verify_email'),
    path('verify-email/resend/', ResendVerificationOTPView.as_view(), name='resend_verification'),
    
    # Password reset with OTP
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Current account
    path('me/', CurrentAccountView.as_view(), name='current_account'),
]