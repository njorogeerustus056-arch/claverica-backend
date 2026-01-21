"""
Main URL Configuration for Claverica Backend
Routes all API endpoints and admin interface
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.db import connection
from django.contrib.auth import get_user_model

# ============================================================================
# CHECK FOR API_URLS MODULE
# ============================================================================
try:
    from backend import api_urls
    API_URLS_AVAILABLE = True
except ImportError as e:
    API_URLS_AVAILABLE = False
    print(f"⚠ Warning: Could not import api_urls: {e}")

# ============================================================================
# ROOT VIEW - Shows basic info
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def root_view(request):
    """Root view that redirects to admin or shows info"""
    return JsonResponse({
        'name': 'Claverica Fintech Backend',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'status': 'operational',
        'environment': 'production' if not settings.DEBUG else 'development',
        'links': {
            'admin_panel': '/admin/',
            'api_root': '/api/' if API_URLS_AVAILABLE else None,
            'health_check': '/health/',
            'api_docs': '/api/docs/' if settings.DEBUG else None,
        },
        'message': 'Backend is running. Use the links above.'
    })

# ============================================================================
# HEALTH CHECK
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'Claverica Backend API',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'debug': settings.DEBUG,
        'environment': 'production' if not settings.DEBUG else 'development',
        'database': settings.DATABASES['default']['ENGINE'],
        'user_model': getattr(settings, 'AUTH_USER_MODEL', 'Not set'),
        'api_available': API_URLS_AVAILABLE,
    })

# ============================================================================
# DATABASE TEST
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def test_database(request):
    """Test database connection endpoint"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        return JsonResponse({
            'status': 'success',
            'database': settings.DATABASES['default']['ENGINE'],
            'connected': True,
            'test_result': result[0] if result else None,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'database': settings.DATABASES['default']['ENGINE'],
            'error': str(e),
            'error_type': type(e).__name__,
            'debug': settings.DEBUG,
            'is_render': 'RENDER' in os.environ,
        }, status=500)

# ============================================================================
# USER MODEL DEBUG
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def user_model_debug(request):
    """Diagnostic endpoint to check user model"""
    try:
        User = get_user_model()
        
        db_name = settings.DATABASES['default'].get('NAME', 'Unknown')
        if hasattr(db_name, '__str__'):
            db_name = str(db_name)
        
        db_host = settings.DATABASES['default'].get('HOST', 'Unknown')
        if db_host and hasattr(db_host, '__str__'):
            db_host = str(db_host)
        
        accounts_position = settings.INSTALLED_APPS.index('accounts') if 'accounts' in settings.INSTALLED_APPS else -1
        apps_before_accounts = []
        if accounts_position >= 0:
            apps_before_accounts = [
                str(app) if hasattr(app, '__str__') else app 
                for app in settings.INSTALLED_APPS[:accounts_position]
            ]
        
        return JsonResponse({
            'status': 'success',
            'AUTH_USER_MODEL': getattr(settings, 'AUTH_USER_MODEL', 'NOT SET'),
            'ACTUAL_USER_MODEL': f'{User.__module__}.{User.__name__}',
            'MODEL_CLASS_NAME': User.__name__,
            'IS_CUSTOM_MODEL': User.__name__ == 'Account',
            'IS_RENDER': 'RENDER' in os.environ,
            'IS_PRODUCTION': not settings.DEBUG,
            'DEBUG': settings.DEBUG,
            'DATABASE_ENGINE': settings.DATABASES['default']['ENGINE'],
            'DATABASE_NAME': db_name,
            'DATABASE_HOST': db_host,
            'CAN_CREATE_USER': hasattr(User, 'email') and hasattr(User, 'password'),
            'USER_MODEL_HAS_EMAIL': hasattr(User, 'email'),
            'USER_MODEL_HAS_USERNAME': hasattr(User, 'username'),
            'API_URLS_AVAILABLE': API_URLS_AVAILABLE,
            'APP_ORDER': {
                'accounts_position': accounts_position,
                'total_apps': len(settings.INSTALLED_APPS),
                'apps_before_accounts': apps_before_accounts
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__,
            'api_urls_available': API_URLS_AVAILABLE,
        }, status=500)

# ============================================================================
# CONDITIONAL IMPORTS FOR DEBUG
# ============================================================================
if settings.DEBUG:
    try:
        from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
        SPECTACULAR_AVAILABLE = True
    except ImportError:
        SPECTACULAR_AVAILABLE = False
        SpectacularAPIView = None
        SpectacularSwaggerView = None
        SpectacularRedocView = None
else:
    SPECTACULAR_AVAILABLE = False

# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    # Root view
    path('', root_view, name='root'),
    
    # Health and diagnostics
    path('health/', health_check, name='health-check'),
    path('test-db/', test_database, name='test-database'),
    path('api/debug/user-model/', user_model_debug, name='user-model-debug'),
    
    # Admin interface
    path('admin/', admin.site.urls),
]

# Add API routes only if available
if API_URLS_AVAILABLE:
    urlpatterns.append(path('api/', include('backend.api_urls')))

# Add API documentation only in DEBUG mode
if settings.DEBUG and SPECTACULAR_AVAILABLE:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development (WhiteNoise handles production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================================
# CUSTOM ADMIN CONFIG
# ============================================================================
admin.site.site_header = "Claverica Admin"
admin.site.site_title = "Claverica Admin Portal"
admin.site.index_title = "Welcome to Claverica Administration"

# ============================================================================
# STARTUP DEBUG
# ============================================================================
if settings.DEBUG:
    print("✓ Django URLs configured")
    print(f"  Root URL pattern count: {len(urlpatterns)}")
    if API_URLS_AVAILABLE:
        print(f"  API endpoints routed through: backend.api_urls")
    else:
        print(f"  ⚠ API endpoints NOT available (api_urls.py missing)")
    print(f"  Debug endpoints enabled")
    
    if SPECTACULAR_AVAILABLE:
        print("✓ DRF Spectacular available for API documentation")
    else:
        print("⚠ DRF Spectacular not installed - API docs disabled")
else:
    print("✓ Production URLs configured")
    print(f"  Allowed hosts: {settings.ALLOWED_HOSTS}")
    print(f"  Debug endpoints disabled")
from .test_view import HealthCheckView, TestTransferView

urlpatterns += [
    path('api/health/', HealthCheckView.as_view(), name='health'),
    path('api/test-transfer/', TestTransferView.as_view(), name='test-transfer'),
]

# Tasks API
path('api/tasks/', include('backend.tasks.urls')),

# Tasks API
path('api/tasks/', include('backend.tasks.urls')),
