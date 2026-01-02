# api_urls.py - UPDATED
"""
API URL Router
Routes all feature app APIs under /api/<app>/
"""
from django.urls import path, include

urlpatterns = [
    # ===================================================
    # ⚠️ REMOVED: Authentication endpoints from here
    # JWT endpoints are now handled by accounts app
    # ===================================================
    
    # Tasks & Rewards API
    path('tasks/', include('tasks.urls')),
    
    # ===================================================
    # ACCOUNTS API (Authentication ONLY)
    # ===================================================
    path('auth/', include('accounts.urls')),
    
    # ===================================================
    # USERS API (User Management ONLY)
    # ===================================================
    path('users/', include('users.urls')),
    
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
    
    # Transfers API
    path('transfers/', include('transfers.urls')),
]