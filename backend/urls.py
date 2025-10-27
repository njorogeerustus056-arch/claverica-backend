"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse  # ✅ Added to handle homepage requests
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# ✅ Simple homepage view to confirm backend is live
def home(request):
    return HttpResponse("✅ Claverica backend is live and running on Render!")

urlpatterns = [
    # ✅ Root URL (homepage)
    path('', home, name='home'),

    # Admin panel
    path('admin/', admin.site.urls),

    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App routes
    path('api/accounts/', include('accounts.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/escrow/', include('escrow.urls')),
    path('api/transactions/', include('transactions.urls')),

    # ✅ Receipts app routes
    path('api/receipts/', include('receipts.urls')),
]
