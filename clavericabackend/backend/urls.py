"""
Main URL Configuration for Claverica Backend
Routes all API endpoints and admin interface
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # ← Back to default (works with your EmailBackend)
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)

from .views import health_check, api_root

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
   
    # Health check endpoint (for Render and monitoring)
    path('health/', health_check, name='health-check'),
   
    # API root
    path('', api_root, name='api-root'),
   
    # JWT Authentication endpoints — CLEAN AND WORKING
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Default view + EmailBackend = email login
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
   
    # API routes - all feature apps under /api/
    path('api/', include('backend.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site configuration
admin.site.site_header = "Claverica Admin"
admin.site.site_title = "Claverica Admin Portal"
admin.site.index_title = "Welcome to Claverica Administration"