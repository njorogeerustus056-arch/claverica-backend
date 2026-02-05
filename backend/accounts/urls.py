from django.urls import path
from .views_account import (
    RegisterView, 
    ActivateView, 
    ResendActivationView,
    LoginView,
    LogoutView,
    PasswordResetView,           # ADD THIS
    PasswordResetConfirmView,    # ADD THIS
    PasswordChangeView          # ADD THIS
)

app_name = 'accounts'

urlpatterns = [
    # Account Registration & Activation
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateView.as_view(), name='activate'),
    path('resend-activation/', ResendActivationView.as_view(), name='resend_activation'),
    
    # Login/Logout
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Password Management (ADD THESE LINES)
    path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
]