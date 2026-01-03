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
from django.db import connection  # ✅ ADD THIS
from django.contrib.auth import get_user_model

# Simple health check endpoint - MAKE PUBLIC
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
        'user_model': getattr(settings, 'AUTH_USER_MODEL', 'Not set'),
    })

# ============================================================================
# CRITICAL: Database Test Endpoint
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def test_database(request):
    """Test database connection endpoint"""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        return JsonResponse({
            'status': 'success',
            'database': settings.DATABASES['default']['ENGINE'],
            'connected': True,
            'test_result': result[0] if result else None,
            'ssl_mode': settings.DATABASES['default'].get('OPTIONS', {}).get('sslmode', 'Not set'),
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
# CRITICAL: User Model Diagnostic Endpoint - FIXED VERSION
# ============================================================================
@api_view(['GET'])
@permission_classes([AllowAny])
def user_model_debug(request):
    """Diagnostic endpoint to check which user model is being used"""
    try:
        User = get_user_model()
        
        # Convert Path objects to strings for JSON serialization
        db_name = settings.DATABASES['default'].get('NAME', 'Unknown')
        if hasattr(db_name, '__str__'):
            db_name = str(db_name)
        
        db_host = settings.DATABASES['default'].get('HOST', 'Unknown')
        if db_host and hasattr(db_host, '__str__'):
            db_host = str(db_host)
        
        # Convert any Path objects in apps_before_accounts to strings
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
            'DATABASE_SSL': settings.DATABASES['default'].get('OPTIONS', {}).get('sslmode', 'Not set'),
            'CAN_CREATE_USER': hasattr(User, 'email') and hasattr(User, 'password'),
            'USER_MODEL_HAS_EMAIL': hasattr(User, 'email'),
            'USER_MODEL_HAS_USERNAME': hasattr(User, 'username'),
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
            'error_type': type(e).__name__
        }, status=500)

# Simple API root - MAKE PUBLIC
@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint"""
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
        'debug_endpoints': debug_endpoints,
        'endpoints': {
            'authentication': {
                'jwt_token': '/api/auth/token/',
                'jwt_refresh': '/api/auth/token/refresh/',
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'pusher_auth': '/api/pusher/auth/',
            },
            'features': {
                'users': '/api/users/',
                'transactions': '/api/transactions/',
                'payments': '/api/payments/',
                'transfers': '/api/transfers/',
            }
        }
    })

# ============================================================================
# Database Reset Endpoint (DEBUG ONLY - REMOVE IN PRODUCTION)
# ============================================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_database_debug(request):
    """DEBUG ONLY: Reset database and create test user"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Not available in production'}, status=403)
    
    try:
        from django.core.management import call_command
        
        # Flush database
        call_command('flush', '--no-input')
        
        # Run migrations
        call_command('migrate')
        
        # Create superuser
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Check if user exists
        if not User.objects.filter(email='admin@claverica.com').exists():
            User.objects.create_superuser(
                email='admin@claverica.com',
                password='admin123'
            )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Database reset successfully',
            'admin_user': 'admin@claverica.com',
            'admin_password': 'admin123'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

# ============================================================================
# Conditional import for drf_spectacular (only in DEBUG mode)
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
    SpectacularAPIView = None
    SpectacularSwaggerView = None
    SpectacularRedocView = None

urlpatterns = [
    # API root and health check
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),
    
    # ============================================================================
    # CRITICAL: Database Test Endpoint (Added)
    # ============================================================================
    path('test-db/', test_database, name='test-database'),
    
    # ============================================================================
    # CRITICAL: User Model Debug Endpoint (Added)
    # ============================================================================
    path('api/debug/user-model/', user_model_debug, name='user-model-debug'),
    
    # ============================================================================
    # DEBUG: Database Reset (Only in development)
    # ============================================================================
    path('api/debug/reset-db/', reset_database_debug, name='reset-db-debug'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # ============================================================================
    # CRITICAL FIX: Correct API routing
    # ============================================================================
    path('api/', include('backend.api_urls')),
]

# Add API documentation only in DEBUG mode
if settings.DEBUG and SPECTACULAR_AVAILABLE:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================================
# Custom admin site configuration
# ============================================================================
admin.site.site_header = "Claverica Admin"
admin.site.site_title = "Claverica Admin Portal"
admin.site.index_title = "Welcome to Claverica Administration"

# ============================================================================
# Add debug message on startup
# ============================================================================
if settings.DEBUG:
    print("✓ Django URLs configured")
    print(f"  Root URL pattern count: {len(urlpatterns)}")
    print(f"  API endpoints routed through: backend.api_urls")
    print(f"  Database test endpoint: /test-db/")
else:
    print("✓ Production URLs configured")
    print(f"  Allowed hosts: {settings.ALLOWED_HOSTS}")
    print(f"  Debug endpoints disabled")