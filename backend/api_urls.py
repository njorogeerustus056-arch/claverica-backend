# api_urls.py
"""
API URL Router
Routes all feature app APIs under /api/<app>/
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    # Authentication endpoints - ADDED THIS SECTION
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Tasks & Rewards API
    path('tasks/', include('tasks.urls')),
    
    # Accounts API
    path('accounts/', include('accounts.urls')),
    
    # Cards API
    path('cards/', include('cards.urls')),
    
    # Compliance API
    path('compliance/', include('compliance.urls')),
    
    # Crypto API
    path('crypto/', include('crypto.urls')),
    
    # Escrow API
    path('escrow/', include('escrow.urls')),
    
    # Notifications API
    path('notifications/', include('notifications.urls')),
    
    # Payments API
    path('payments/', include('payments.urls')),
    
    # Receipts API
    path('receipts/', include('receipts.urls')),
    
    # Transactions API
    path('transactions/', include('transactions.urls')),
]