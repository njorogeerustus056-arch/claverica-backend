from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def health_check(request):
    """Simple health check that always returns 200"""
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    # Handle health check with AND without trailing slash
    path('health', health_check, name='health_check_no_slash'),
    path('health/', health_check, name='health_check'),
    path('', health_check, name='root_health'),
    path('admin/', admin.site.urls),
    # Add your other URLs below
]
