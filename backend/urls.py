from django.urls import path, include
from django.http import JsonResponse
from django.contrib import admin
import time

# ========== HEALTH CHECK ==========
def health_check(request):
    return JsonResponse({"status": "ok", "timestamp": time.time()}, status=200)

# Import your views
from accounts.views_account import (
    RegisterView, ActivateView, ResendActivationView,
    LoginView, PasswordResetView, PasswordResetConfirmView,
    PasswordChangeView, LogoutView
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from users.views import user_profile, user_me
from payments import urls as payments_urls
from transfers import urls as transfers_urls
from kyc import urls as kyc_urls
from notifications import urls as notifications_urls
from compliance.urls import api_urlpatterns as compliance_api_urls
from kyc_spec import urls as kyc_spec_urls

from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def debug_notifications(request):
    return Response({'message': 'Notifications debug endpoint working'})

@api_view(['GET'])
def debug_kyc_spec(request):
    return Response({'message': 'KYC Spec Dumpster is running'})

@api_view(['GET'])
def api_root(request):
    return Response({'message': 'API Running'})

@api_view(['POST'])
def pusher_auth(request):
    return Response({'auth': 'key:signature123'})

@api_view(['GET'])
def compliance_status(request):
    return Response({'status': 'verified'})

@api_view(['GET'])
def savings_pots(request):
    return Response({'pots': [], 'total': 0, 'total_target': 0})

urlpatterns = [
    # HEALTH CHECK - MUST BE FIRST
    path('health/', health_check, name='health_check'),
    path('', health_check, name='root_health'),
    
    path('api/kyc/', include(kyc_urls)),
    path('api/kyc-spec/', include(kyc_spec_urls)),
    path('api/accounts/register/', RegisterView.as_view(), name='account_register'),
    path('api/accounts/activate/', ActivateView.as_view(), name='account_activate'),
    path('api/accounts/resend-activation/', ResendActivationView.as_view(), name='resend_activation'),
    path('api/accounts/login/', LoginView.as_view(), name='account_login'),
    path('api/accounts/logout/', LogoutView.as_view(), name='account_logout'),
    path('api/accounts/password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('api/accounts/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/accounts/password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('api/accounts/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/users/profile/', user_profile),
    path('api/users/me/', user_me),
    path('api/transactions/', include('transactions.urls')),
    path('api/payments/', include(payments_urls)),
    path('api/transfers/', include(transfers_urls)),
    path('api/compliance/', include(compliance_api_urls)),
    path('api/cards/', include('cards.urls')),
    path('api/', api_root),
    path('api/pusher/auth/', pusher_auth),
    path('api/compliance/status/', compliance_status),
    path('api/notifications/', include(notifications_urls)),
    path('api/debug/notifications/', debug_notifications),
    path('api/debug/kyc-spec/', debug_kyc_spec),
    path('api/savings/pots/', savings_pots),
    path('admin/', admin.site.urls),
]
