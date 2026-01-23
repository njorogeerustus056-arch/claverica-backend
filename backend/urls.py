from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
import hashlib

# ========== AUTH ==========
@api_view(['POST'])
def login_endpoint(request):
    return Response({
        'success': True,
        'token': 'token-123',
        'user': {'id': 1, 'email': 'admin@claverica.com'}
    })

@api_view(['GET'])
def user_profile(request):
    return Response({
        'id': 1,
        'email': 'admin@claverica.com'
    })

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

# ========== NOTIFICATIONS ==========
@api_view(['GET'])
def notifications_all(request):
    return Response({'notifications': []})

urlpatterns = [
    # Auth
    path('api/auth/login/', login_endpoint),
    path('api/auth/refresh/', login_endpoint),
    
    # User
    path('api/users/profile/', user_profile),
    path('api/users/me/', user_profile),
    
    # Pusher
    path('api/pusher/auth/', pusher_auth),
    
    # Compliance
    path('api/compliance/status/', compliance_status),
    path('api/compliance/getStatus/', compliance_status),
    
    # Notifications
    path('api/notifications/all/', notifications_all),
    path('api/notifications/getAll/', notifications_all),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Home
    path('', lambda r: HttpResponse('API Running')),
]
