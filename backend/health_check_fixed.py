from django.http import JsonResponse
import time

def railway_health_check(request):
    """Ultra simple health check - ALWAYS returns 200 OK"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'claverica-backend'
    }, status=200)
