from django.http import HttpResponse
from django.urls import path

def health_check(request):
    """Simple health check - ALWAYS returns 200 OK"""
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', health_check, name='root_health'),  # Also handle root
]
