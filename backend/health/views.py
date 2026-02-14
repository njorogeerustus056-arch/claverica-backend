# backend/health/views.py
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """
    Enhanced health check that verifies database connection
    Used by Railway for health monitoring
    """
    health_status = {
        'status': 'healthy',
        'database': 'connected',
        'timestamp': str(timezone.now()),
        'details': {}
    }
    
    # Check database connection
    db_conn = connections['default']
    try:
        db_conn.cursor().execute('SELECT 1')
        health_status['database'] = 'connected'
    except OperationalError as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = 'disconnected'
        health_status['details']['database_error'] = str(e)
        logger.error(f"Health check database error: {e}")
    
    # Check if app is responding
    try:
        from django.apps import apps
        apps.check_apps_ready()
        health_status['apps_ready'] = True
    except Exception as e:
        health_status['apps_ready'] = False
        health_status['details']['apps_error'] = str(e)
    
    # Return appropriate status code
    status_code = 200 if health_status['status'] == 'healthy' else 500
    return JsonResponse(health_status, status=status_code)

@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check for Kubernetes/Railway
    Checks if app is ready to accept traffic
    """
    return JsonResponse({'status': 'ready'}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check for Kubernetes/Railway
    Basic check if app is alive
    """
    return JsonResponse({'status': 'alive'}, status=200)