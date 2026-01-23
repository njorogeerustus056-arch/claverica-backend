from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse

# ========== AUTH ==========
@api_view(['POST'])
def login_endpoint(request):
    return Response({
        'success': True,
        'token': 'token-123',
        'refresh': 'refresh-456',
        'user': {'id': 1, 'email': 'admin@claverica.com'}
    })

@api_view(['POST'])
def auth_refresh(request):
    return Response({
        'access': 'new-token',
        'refresh': 'new-refresh'
    })

# ========== USER ==========
@api_view(['GET'])
def user_profile(request):
    return Response({
        'id': 1,
        'email': 'admin@claverica.com',
        'name': 'Emergency User'
    })

@api_view(['GET'])
def user_me(request):
    return Response({
        'id': 1,
        'email': 'admin@claverica.com'
    })

# ========== API ==========
@api_view(['GET']) 
def api_root(request):
    return Response({'message': 'API Running'})

@api_view(['GET'])
def transactions_list(request):
    return Response({'transactions': [{'id': 1}]})

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

# ========== HOME ==========
def home(request):
    return HttpResponse('Claverica Banking API')

# ========== URL PATTERNS ==========
urlpatterns = [
    # Auth
    path('api/auth/login/', login_endpoint),
    path('api/auth/refresh/', auth_refresh),
    path('api/token/refresh/', auth_refresh),
    
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
