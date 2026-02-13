from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.contrib import admin
import time

# SIMPLE HEALTH CHECK - RETURNS 200 OK
def health_check(request):
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health', health_check, name='health_check_no_slash'),
    path('admin/', admin.site.urls),
]
