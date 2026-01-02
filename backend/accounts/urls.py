# accounts/urls.py - Make sure all paths end with /
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    IndexView,
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    PasswordResetView,
    PasswordResetConfirmView,
    EmailVerificationView,
    ResendEmailVerificationView,
    CurrentAccountView
)

app_name = 'accounts'

urlpatterns = [
    # Health check
    path('', IndexView.as_view(), name='index'),
    
    # Authentication - ALL WITH TRAILING SLASHES
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password management
    path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('verify-email/resend/', ResendEmailVerificationView.as_view(), name='resend_verification'),
    
    # Current account (minimal)
    path('me/', CurrentAccountView.as_view(), name='current_account'),
]