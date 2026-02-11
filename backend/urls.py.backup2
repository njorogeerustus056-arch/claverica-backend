from health_check import railway_health_check
from railway_health import railway_health_check
from django.http import JsonResponse
import time

# ========== SIMPLE HEALTH CHECK FOR RAILWAY ==========
def railway_health(request):
    """Simplest possible health check - ALWAYS returns 200"""
    return JsonResponse({
        "status": "ok",
        "timestamp": time.time()
    })
from django.urls import path, include
from django.http import JsonResponse
import time
from accounts.views_account import (
    RegisterView, 
    ActivateView, 
    ResendActivationView, 
    LoginView,
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordChangeView,
    LogoutView
)
from django.contrib import admin
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from users.views import user_profile, user_me

# JWT token views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Import app URLs
from payments import urls as payments_urls
from transfers import urls as transfers_urls
from kyc import urls as kyc_urls
from notifications import urls as notifications_urls
from compliance.urls import api_urlpatterns as compliance_api_urls
from kyc_spec import urls as kyc_spec_urls

# ========== DEBUG ENDPOINTS ==========
@api_view(['GET'])
def debug_notifications(request):
    """Debug endpoint to verify notifications URLs are loaded"""
    return Response({
        'message': '✅ Notifications debug endpoint working',
        'endpoints': {
            'unread_count': '/api/notifications/unread-count/',
            'list': '/api/notifications/',
            'mark_read': '/api/notifications/mark-read/<id>/',
            'mark_all_read': '/api/notifications/mark-all-read/',
            'admin_alerts': '/api/notifications/admin/alerts/',
            'preferences': '/api/notifications/preferences/'
        }
    })

@api_view(['GET'])
def debug_kyc_spec(request):
    """Debug endpoint for KYC Spec dumpster"""
    return Response({
        'message': '✅ KYC Spec Dumpster is running',
        'endpoints': {
            'collect': '/api/kyc-spec/collect/',
            'collect_legacy': '/api/kyc-spec/collect-legacy/',
            'stats': '/api/kyc-spec/stats/'
        }
    })

# ========== API ==========
@api_view(['GET'])
def api_root(request):
    return Response({'message': 'API Running'})

# ========== PUSHER ==========
@api_view(['POST'])
def pusher_auth(request):
    return Response({
        'auth': 'key:signature123'
    })

# ========== COMPLIANCE ==========
@api_view(['GET'])
def compliance_status(request):
    return Response({'status': 'verified'})

# ========== SAVINGS ==========
@api_view(['GET'])
def savings_pots(request):
    return Response({
        'pots': [
            {
                'id': 1,
                'name': 'Emergency Fund',
                'balance': 1250.50,
                'target': 5000,
                'color': '#4CAF50'
            },
            {
                'id': 2,
                'name': 'Vacation 2024',
                'balance': 850.75,
                'target': 2000,
                'color': '#2196F3'
            }
        ],
        'total': 2101.25,
        'total_target': 7000
    })

# ========== HOME ==========
def home(request):
    """Root health check endpoint for Railway"""
    from django.db import connection
    from django.db.utils import OperationalError
    
    # Check database connection
    db_connected = False
    try:
        connection.ensure_connection()
        db_connected = True
    except OperationalError:
        db_connected = False
    
    import time
    return JsonResponse({
        "status": "healthy",
        "service": "Claverica Banking API",
        "timestamp": time.time(),
        "database": "connected" if db_connected else "disconnected",
        "debug": False  # Change based on your DEBUG setting
    })

# ========== URL PATTERNS ==========
urlpatterns = [
    path('', railway_health_check, name='health_check_root'),
    path('health/', health_check_200, name='health_check'),
    # CRITICAL: SIMPLE HEALTH CHECK FOR RAILWAY - MUST BE FIRST
    ,
    # Root health check - MUST BE FIRST for Railway
    ,
    path('health/', lambda request: JsonResponse({'status': 'ok', 'timestamp': time.time()})),
    # KYC endpoints
    path('api/kyc/', include(kyc_urls)),

    # KYC SPEC DUMPSTER ENDPOINTS
    path('api/kyc-spec/', include(kyc_spec_urls)),

    # ✅✅✅ ACCOUNT ENDPOINTS - COMPLETE AUTH
    path('api/accounts/register/', RegisterView.as_view(), name='account_register'),
    path('api/accounts/activate/', ActivateView.as_view(), name='account_activate'),
    path('api/accounts/resend-activation/', ResendActivationView.as_view(), name='resend_activation'),
    path('api/accounts/login/', LoginView.as_view(), name='account_login'),
    path('api/accounts/logout/', LogoutView.as_view(), name='account_logout'),  # NEW
    path('api/accounts/password/reset/', PasswordResetView.as_view(), name='password_reset'),  # NEW
    path('api/accounts/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  # NEW
    path('api/accounts/password/change/', PasswordChangeView.as_view(), name='password_change'),  # NEW
    path('api/accounts/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # User endpoints
    path('api/users/profile/', user_profile),
    path('api/users/me/', user_me),

    # Transactions endpoints
    path('api/transactions/', include('transactions.urls')),

    # Payments endpoints
    path('api/payments/', include(payments_urls)),

    # Transfers endpoints
    path('api/transfers/', include(transfers_urls)),

    # Compliance endpoints
    path('api/compliance/', include(compliance_api_urls)),

    # Cards endpoints
    path('api/cards/', include('cards.urls')),

    # API
    path('api/', api_root),

    # Pusher
    path('api/pusher/auth/', pusher_auth),

    # Compliance status
    path('api/compliance/status/', compliance_status),

    # Notifications endpoints
    path('api/notifications/', include(notifications_urls)),

    # Debug endpoints
    path('api/debug/notifications/', debug_notifications),
    path('api/debug/kyc-spec/', debug_kyc_spec),

    # Savings
    path('api/savings/pots/', savings_pots),

    # Admin
    path('admin/', admin.site.urls)
]







