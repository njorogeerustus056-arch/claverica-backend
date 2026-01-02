# urls.py - UPDATED
"""
Main URL Configuration for Claverica Backend
Routes all API endpoints and admin interface
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse

# Simple health check endpoint
@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Claverica Backend API',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'debug': settings.DEBUG
    })

# Simple API root
@api_view(['GET'])
def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'name': 'Claverica Fintech API',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'documentation': '/api/docs/' if settings.DEBUG else None,
        'endpoints': {
            'admin': '/admin/',
            'auth': '/api/auth/',
            'users': '/api/users/',
            'transactions': '/api/transactions/',
        }
    })

# Simple pusher auth stub
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pusher_auth(request):
    """Pusher authentication stub"""
    return JsonResponse({'error': 'Pusher not configured'}, status=501)

urlpatterns = [
    # Health check and API root
    path('health/', health_check, name='health-check'),
    path('', api_root, name='api-root'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Pusher auth
    path('api/pusher/auth/', pusher_auth, name='pusher-auth'),
    
    # Main API routes (includes both accounts and users)
    path('api/', include('api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site configuration
admin.site.site_header = "Claverica Admin"
admin.site.site_title = "Claverica Admin Portal"
admin.site.index_title = "Welcome to Claverica Administration"