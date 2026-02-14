from django.urls import path, include
from django.http import HttpResponse
from django.contrib import admin
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone  # Add this for timestamp
import json  # Add this for JSON responses

# Simple health check for Railway
@csrf_exempt
@require_GET
def health_check(request):
    """Basic health check endpoint"""
    return HttpResponse("OK", status=200, content_type="text/plain")

# Enhanced health check with database verification
@csrf_exempt
@require_GET
def detailed_health_check(request):
    """Enhanced health check that verifies database connection"""
    from django.db import connections
    from django.db.utils import OperationalError
    
    health_status = {
        'status': 'healthy',
        'database': 'connected',
        'timestamp': str(timezone.now()),
    }
    
    # Check database connection
    try:
        db_conn = connections['default']
        db_conn.cursor().execute('SELECT 1')
    except OperationalError:
        health_status['status'] = 'unhealthy'
        health_status['database'] = 'disconnected'
        return HttpResponse(
            json.dumps(health_status), 
            status=500, 
            content_type="application/json"
        )
    
    return HttpResponse(
        json.dumps(health_status), 
        status=200, 
        content_type="application/json"
    )

urlpatterns = [
    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('health', health_check, name='health_check_no_slash'),
    path('health/detailed/', detailed_health_check, name='detailed_health'),
    
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/users/', include('users.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/cards/', include('cards.urls')),
]