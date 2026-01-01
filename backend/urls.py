# urls.py
"""
Main URL Configuration for Claverica Backend
Routes all API endpoints and admin interface
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Simple user profile endpoint
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Simple user profile endpoint that matches frontend expectations"""
    user = request.user
    
    # Debug logging
    print(f"[USER PROFILE] Request from user: {user.id} - {user.email}")
    
    # Extract basic user info
    email_prefix = user.email.split('@')[0] if user.email else 'user'
    
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': getattr(user, 'first_name', ''),
        'last_name': getattr(user, 'last_name', ''),
        'name': f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or email_prefix.title(),
        'account_number': getattr(user, 'account_number', f'ACC{user.id:08d}'),
        'balance': float(getattr(user, 'balance', 0.0)),
        'ip_address': request.META.get('REMOTE_ADDR', '192.168.1.1'),
    })

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # User profile endpoint
    path('api/user/profile/', user_profile, name='user-profile'),
]

# Try to import views safely
try:
    import views
    urlpatterns += [
        path('health/', views.health_check, name='health-check'),
        path('', views.api_root, name='api-root'),
        path('api/pusher/auth/', views.pusher_auth, name='pusher-auth'),
    ]
except ImportError as e:
    print(f"Note: Could not import views: {e}")

# Try to include api_urls safely
try:
    urlpatterns += [
        path('api/', include('api_urls')),
    ]
except Exception as e:
    print(f"Note: Could not include api_urls: {e}")

# DEBUG TOOLBAR FIX - Add this conditionally
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        print("Note: Debug toolbar not installed")

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site configuration
admin.site.site_header = "Claverica Admin"
admin.site.site_title = "Claverica Admin Portal"
admin.site.index_title = "Welcome to Claverica Administration"