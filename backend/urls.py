from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        "status": "healthy",
        "service": "claverica-backend",
        "database": "connected",
        "timestamp": "2026-02-13"
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    # Add your API URLs here
    # path('api/', include('accounts.urls')),
    # path('api/', include('transactions.urls')),
]