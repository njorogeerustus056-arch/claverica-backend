from django.urls import path
from django.http import HttpResponse
from django.contrib import admin

def health_check(request):
    return HttpResponse("OK", status=200, content_type="text/plain")

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health', health_check, name='health_check_no_slash'),
    path('admin/', admin.site.urls),
]
