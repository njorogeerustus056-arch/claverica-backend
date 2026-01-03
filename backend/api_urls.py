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
# Simple API Welcome Endpoint
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def api_welcome(request):
    """API welcome endpoint"""
    from django.conf import settings
    
    return JsonResponse({
        'message': 'Welcome to Claverica Fintech API',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'status': 'operational',
        'environment': 'development' if os.environ.get('DEBUG') == 'True' else 'production',
        'user_model': getattr(settings, 'AUTH_USER_MODEL', 'Not set'),
        'endpoints': {
            'authentication': {
                'jwt_token': '/api/auth/token/',
                'jwt_refresh': '/api/auth/token/refresh/',
                'jwt_verify': '/api/auth/token/verify/',
                'jwt_blacklist': '/api/auth/token/blacklist/',
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'pusher_auth': '/api/pusher/auth/',
            },
            'features': {
                'users': '/api/users/',
                'tasks': '/api/tasks/',
                'cards': '/api/cards/',
                'transactions': '/api/transactions/',
                'payments': '/api/payments/',
                'transfers': '/api/transfers/',
                'crypto': '/api/crypto/',
                'escrow': '/api/escrow/',
                'receipts': '/api/receipts/',
                'compliance': '/api/compliance/',
                'notifications': '/api/notifications/',
            },
            'debug': {
                'user_model_check': '/api/debug/user-model/',
                'health': '/health/',
            } if os.environ.get('DEBUG') == 'True' else {}
        }
    })

# ============================================================================
# Custom Token Obtain Pair View (if needed for email-based auth)
# ============================================================================
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['user_id'] = str(user.id)
        token['is_active'] = user.is_active
        token['is_staff'] = user.is_staff
        
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    # ===================================================
    # API Welcome Endpoint (Root of /api/)
    # ===================================================
    path('', api_welcome, name='api-welcome'),
    
    # ===================================================
    # SimpleJWT Authentication endpoints
    # ===================================================
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # ===================================================
    # Custom Accounts Authentication
    # ===================================================
    path('auth/', include('accounts.urls')),  # This adds /register/, /login/, etc
    
    # ===================================================
    # Pusher Authentication (from your views.py)
    # ===================================================
    path('pusher/auth/', pusher_auth, name='pusher-auth'),
    
    # ===================================================
    # Feature APIs
    # ===================================================
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
# Debug output
# ============================================================================
if os.environ.get('DEBUG') == 'True':
    print("✓ API URLs configured")
    print(f"  Total API endpoints: {len(urlpatterns)}")
    print(f"  Pusher auth endpoint: /api/pusher/auth/")