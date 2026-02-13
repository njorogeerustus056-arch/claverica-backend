from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        "status": "healthy",
        "service": "claverica-backend",
        "database": "connected"
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    # Add your app URLs here
    # path('api/accounts/', include('accounts.urls')),
    # path('api/transactions/', include('transactions.urls')),
]
