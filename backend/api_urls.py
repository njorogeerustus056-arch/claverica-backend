"""
API URL Configuration for Claverica Backend
Routes all API endpoints to their respective apps
"""
import os
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.conf import settings

# Try to import pusher_auth with error handling
try:
    from backend.views import pusher_auth
    PUSHER_AUTH_AVAILABLE = True
except ImportError:
    PUSHER_AUTH_AVAILABLE = False
    print("⚠ Warning: pusher_auth view not found in backend.views")
    # Create a placeholder function
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def pusher_auth(request):
        return JsonResponse({
            'error': 'Pusher authentication not configured',
            'detail': 'backend.views.pusher_auth not found'
        }, status=501)

# ============================================================================
# API ROOT ENDPOINT
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint that shows available endpoints"""
    from django.conf import settings
    
    # Build endpoints dictionary
    endpoints = {
        'authentication': {
            'jwt_token': '/api/auth/token/',
            'jwt_refresh': '/api/auth/token/refresh/',
            'jwt_verify': '/api/auth/token/verify/',
            'jwt_blacklist': '/api/auth/token/blacklist/',
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'pusher_auth': '/api/pusher/auth/' if PUSHER_AUTH_AVAILABLE else None,
        },
        'user_management': {
            'users': '/api/users/',
            'user_profile': '/api/users/profile/',
            'user_update': '/api/users/update/',
        },
        'features': {
            'transactions': '/api/transactions/',
            'backend.payments': '/api/payments/',
            'backend.transfers': '/api/transfers/',
            'backend.cards': '/api/cards/',
            'backend.crypto': '/api/crypto/',
            'backend.escrow': '/api/escrow/',
            'receipts': '/api/receipts/',
            'notifications': '/api/notifications/',
        }
    }
    
    # Filter out None values
    for category in endpoints:
        endpoints[category] = {k: v for k, v in endpoints[category].items() if v is not None}
    
    debug_endpoints = {
        'user_model_check': '/api/debug/user-model/',
        'health_check': '/health/',
        'test_database': '/test-db/',
        'admin': '/admin/',
    } if settings.DEBUG else {}
    
    return JsonResponse({
        'name': 'Claverica Fintech API',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'status': 'operational',
        'environment': 'production' if not settings.DEBUG else 'development',
        'documentation': '/api/docs/' if settings.DEBUG else None,
        'authentication_required': True,
        'authentication_methods': ['JWT Bearer Token'],
        'pusher_available': PUSHER_AUTH_AVAILABLE,
        'debug_endpoints': debug_endpoints,
        'endpoints': endpoints,
        'cors_enabled': True,
        'cors_allowed_origins': getattr(settings, 'CORS_ALLOWED_ORIGINS', [])[:3],  # Show first 3
    })

# ============================================================================
# CUSTOM TOKEN VIEW FOR EMAIL AUTH
# ============================================================================
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims for React frontend
        token['email'] = user.email
        token['user_id'] = str(user.id)
        token['is_active'] = user.is_active
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
        return token
    
    def validate(self, attrs):
        # Allow email or username login
        data = super().validate(attrs)
        
        # Add user info to response
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': getattr(user, 'first_name', ''),
            'last_name': getattr(user, 'last_name', ''),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# ============================================================================
# APP URL AVAILABILITY CHECK
# ============================================================================
def check_app_urls(app_name, url_path):
    """Check if an app's urls.py exists and is importable"""
    try:
        module = __import__(f'{app_name}.urls', fromlist=['urlpatterns'])
        return True, getattr(module, 'urlpatterns', [])
    except ImportError:
        return False, []

# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    # API Root (shows all endpoints)
    path('', api_root, name='api-root'),
    
    # ======================
    # AUTHENTICATION
    # ======================
    # JWT Endpoints
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # Custom Auth Endpoints (from accounts app)
    path('auth/', include('backend.accounts.urls')),
    
    # Pusher Authentication
    path('pusher/auth/', pusher_auth, name='pusher-auth'),
]

# ======================
# DYNAMICALLY ADD FEATURE APIS
# ======================
feature_apps = [
    ('users', 'users/'),
    ('backend.claverica_tasks', 'tasks/'),
    ('backend.cards', 'cards/'),
    ('backend.compliance', 'compliance/'),
    ('backend.crypto', 'crypto/'),
    ('backend.escrow', 'escrow/'),
    ('notifications', 'notifications/'),
    ('backend.payments', 'payments/'),
    ('receipts', 'receipts/'),
    ('transactions', 'transactions/'),
    ('backend.transfers', 'transfers/'),
]

for app_name, url_prefix in feature_apps:
    is_available, _ = check_app_urls(app_name, url_prefix)
    if is_available:
        urlpatterns.append(path(url_prefix, include(f'{app_name}.urls')))
        if settings.DEBUG:
            print(f"  ✓ {app_name} API endpoints added: /api/{url_prefix}")
    elif settings.DEBUG:
        print(f"  ⚠ {app_name} API endpoints NOT available: {app_name}/urls.py not found")

# ============================================================================
# DEBUG OUTPUT
# ============================================================================
if settings.DEBUG:
    print("✓ API URLs configured for React integration")
    print(f"  Total API endpoints: {len(urlpatterns)}")
    print(f"  JWT endpoints available")
    if PUSHER_AUTH_AVAILABLE:
        print(f"  Pusher auth: /api/pusher/auth/")
    else:
        print(f"  ⚠ Pusher auth NOT configured")
    print(f"  CORS enabled for React")