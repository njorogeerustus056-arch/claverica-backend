from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse

# ========== AUTH ENDPOINTS ==========
@api_view(['POST'])
def emergency_login(request):
    return Response({
        'success': True,
        'message': 'Login successful',
        'token': 'emergency-token-123',
        'refresh_token': 'refresh-token-456',
        'user': {
            'id': 1,
            'email': 'admin@claverica.com',
            'first_name': 'Emergency',
            'last_name': 'User'
        }
    })

@api_view(['POST'])
def token_refresh(request):
    return Response({
        'access': 'new-access-token',
        'refresh': 'new-refresh-token'
    })

# ========== USER ENDPOINTS ==========
@api_view(['GET'])
def user_profile(request):
    return Response({
        'id': 1,
        'email': 'admin@claverica.com',
        'first_name': 'Emergency',
        'last_name': 'User',
        'balance': 5000.00
    })

@api_view(['GET'])
def user_me(request):
    return Response({
        'id': 1,
        'email': 'admin@claverica.com',
        'name': 'Emergency User'
    })

# ========== API ENDPOINTS ==========
@api_view(['GET']) 
def api_root(request):
    return Response({
        'message': 'Claverica Banking API',
        'version': '1.0'
    })

@api_view(['GET'])
def transactions_list(request):
    return Response({
        'count': 3,
        'results': [
            {'id': 1, 'amount': 100, 'type': 'deposit'},
            {'id': 2, 'amount': 50, 'type': 'withdrawal'},
            {'id': 3, 'amount': 200, 'type': 'transfer'}
        ]
    })

# ========== PUSHER AUTH ==========
@api_view(['POST'])
def pusher_auth(request):
    return Response({
        'auth': 'pusher-auth-key-123'
    })

# ========== COMPLIANCE ==========
@api_view(['GET'])
def compliance_status(request):
    return Response({
        'status': 'verified',
        'level': 'full'
    })

# ========== NOTIFICATIONS ==========
@api_view(['GET'])
def notifications_all(request):
    return Response({
        'count': 2,
        'notifications': [
            {'id': 1, 'message': 'Welcome to Claverica!', 'read': False},
            {'id': 2, 'message': 'Your account is ready', 'read': True}
        ]
    })

# ========== HOME PAGE ==========
def home(request):
    return HttpResponse('Claverica Banking API - Emergency Mode')

# ========== URL PATTERNS ==========
urlpatterns = [
    # Auth
    path('api/auth/login/', emergency_login),
    path('api/emergency-login/', emergency_login),
    path('api/token/refresh/', token_refresh),
    
    # User
    path('api/users/profile/', user_profile),
    path('api/users/me/', user_me),
    
    # API
    path('api/', api_root),
    path('api/transactions/', transactions_list),
    
    # Pusher
    path('api/pusher/auth/', pusher_auth),
    
    # Compliance
    path('api/compliance/status/', compliance_status),
    
    # Notifications
    path('api/notifications/all/', notifications_all),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Home
    path('', home),
]
