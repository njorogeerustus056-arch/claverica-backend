from django.contrib import admin
from django.urls import path, include
from health_check import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    # Add your app URLs here - uncomment when ready
    # path('api/accounts/', include('accounts.urls')),
    # path('api/transactions/', include('transactions.urls')),
]
