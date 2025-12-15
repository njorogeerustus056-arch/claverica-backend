"""
URL configuration for backend project.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static

# ✅ Simple homepage view to confirm backend is live
def home(request):
    return JsonResponse({
        "status": "success",
        "message": "✅ Claverica backend is live and running!",
        "version": "1.0.0",
        "endpoints": {
            "admin": "/admin/",
            "token": "/api/token/",
            "accounts": "/api/accounts/",
            "payments": "/api/payments/",
            "escrow": "/api/escrow/",
            "transactions": "/api/transactions/",
        }
    })

# ✅ Health check endpoint for monitoring
@csrf_exempt
def health_check(request):
    """Health check endpoint for Render and monitoring services"""
    from django.db import connection
    
    try:
        # Check database connection
        connection.ensure_connection()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return JsonResponse({
        "status": "healthy",
        "database": db_status,
        "service": "claverica-backend"
    })

urlpatterns = [
    # ✅ Root URL (homepage)
    path('', home, name='home'),
    
    # ✅ Health check endpoint
    path('health/', health_check, name='health_check'),

    # Admin panel
    path('admin/', admin.site.urls),

    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App routes
    path('api/accounts/', include('accounts.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/escrow/', include('escrow.urls')),
    path('api/transactions/', include('transactions.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
