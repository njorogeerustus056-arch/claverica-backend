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
from backend.views import pusher_auth

# ============================================================================
# API ROOT ENDPOINT
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint that shows available endpoints"""
    from django.conf import settings
    
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
        'debug_endpoints': debug_endpoints,
        'endpoints': {
            'authentication': {
                'jwt_token': '/api/auth/token/',
                'jwt_refresh': '/api/auth/token/refresh/',
                'jwt_verify': '/api/auth/token/verify/',
                'jwt_blacklist': '/api/auth/token/blacklist/',
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'pusher_auth': '/api/pusher/auth/',
            },
            'user_management': {
                'users': '/api/users/',
                'user_profile': '/api/users/profile/',
                'user_update': '/api/users/update/',
            },
            'features': {
                'transactions': '/api/transactions/',
                'payments': '/api/payments/',
                'transfers': '/api/transfers/',
                'cards': '/api/cards/',
                'crypto': '/api/crypto/',
                'escrow': '/api/escrow/',
                'receipts': '/api/receipts/',
                'notifications': '/api/notifications/',
            }
        },
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
    path('auth/', include('accounts.urls')),
    
    # Pusher Authentication
    path('pusher/auth/', pusher_auth, name='pusher-auth'),
    
    # ======================
    # FEATURE APIS
    # ======================
    path('users/', include('users.urls')),
    path('tasks/', include('tasks.urls')),
    path('cards/', include('cards.urls')),
    path('compliance/', include('compliance.urls')),
    path('crypto/', include('crypto.urls')),
    path('escrow/', include('escrow.urls')),
    path('notifications/', include('notifications.urls')),
    path('payments/', include('payments.urls')),
    path('receipts/', include('receipts.urls')),
    path('transactions/', include('transactions.urls')),
    path('transfers/', include('transfers.urls')),
]

# ============================================================================
# DEBUG OUTPUT
# ============================================================================
if os.environ.get('DEBUG') == 'True':
    print("✓ API URLs configured for React integration")
    print(f"  Total API endpoints: {len(urlpatterns)}")
    print(f"  JWT endpoints available")
    print(f"  Pusher auth: /api/pusher/auth/")
    print(f"  CORS enabled for React")