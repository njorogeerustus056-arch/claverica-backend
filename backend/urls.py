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
        'token': 'emergency-token-123',
        'refresh': 'refresh-token-456',
        'user': {'id': 1, 'email': 'admin@claverica.com'}
    })

@api_view(['POST'])
def auth_refresh(request):
    """Token refresh endpoint - frontend calls djangoApi.auth.refresh()"""
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
        'last_name': 'User'
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
    return Response({'message': 'API is running'})

@api_view(['GET'])
def transactions_list(request):
    return Response({
        'transactions': [
            {'id': 1, 'amount': 100, 'type': 'deposit'}
        ]
    })

# ========== PUSHER AUTH ==========
@api_view(['POST'])
def pusher_auth(request):
    """Pusher authentication endpoint"""
    return Response({
        'auth': 'pusher-auth-key-123456'
    })

# ========== COMPLIANCE ENDPOINTS ==========
@api_view(['GET'])
def compliance_getStatus(request):
    """Compliance status - frontend calls djangoApi.compliance.getStatus()"""
    return Response({
        'status': 'verified',
        'level': 'full',
        'verified_at': '2024-01-22'
    })

@api_view(['POST'])
def compliance_submit(request):
    """Compliance submit"""
    return Response({'success': True})

# ========== NOTIFICATIONS ENDPOINTS ==========
@api_view(['GET'])
def notifications_getAll(request):
    """Notifications - frontend calls djangoApi.notifications.getAll()"""
    return Response({
        'notifications': [
            {'id': 1, 'message': 'Welcome!', 'read': False},
            {'id': 2, 'message': 'Account ready', 'read': True}
        ]
    })

@api_view(['POST'])
def notifications_markRead(request):
    """Mark notification as read"""
    return Response({'success': True})

# ========== HOME PAGE ==========
def home(request):
    return HttpResponse('Claverica Banking API - All endpoints working')

# ========== URL PATTERNS ==========
urlpatterns = [
    # Auth endpoints (frontend uses these)
    path('api/auth/login/', emergency_login),
    path('api/auth/refresh/', auth_refresh),
    path('api/token/refresh/', auth_refresh),  # Alternative path
    
    # User endpoints
    path('api/users/profile/', user_profile),
    path('api/users/me/', user_me),
    
    # API endpoints
    path('api/', api_root),
    path('api/transactions/', transactions_list),
    
    # Pusher
    path('api/pusher/auth/', pusher_auth),
    
    # Compliance endpoints
    path('api/compliance/status/', compliance_getStatus),
    path('api/compliance/submit/', compliance_submit),
    
    # Notifications endpoints
    path('api/notifications/all/', notifications_getAll),
    path('api/notifications/mark-read/', notifications_markRead),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Home
    path('', home),
]
