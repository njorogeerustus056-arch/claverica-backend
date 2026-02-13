from django.contrib import admin
from django.urls import path
from health_simple import health_check

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health', health_check, name='health_check_no_slash'),
    path('admin/', admin.site.urls),
]
