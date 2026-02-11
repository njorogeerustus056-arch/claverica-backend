from django.http import JsonResponse
import time

def railway_health_check(request):
    """Simple health check for Railway that always returns 200"""
    return JsonResponse({
        "status": "healthy",
        "service": "Claverica Banking API",
        "timestamp": time.time(),
        "message": "API is running",
        "database": "check_skipped"  # Don't check DB on health check
    })

# Simple test endpoint
def simple_test(request):
    return JsonResponse({"message": "Test OK"})
