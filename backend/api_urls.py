# api_urls.py - FIXED VERSION
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from backend.views import pusher_auth

urlpatterns = [
    # ===================================================
    # SimpleJWT Authentication endpoints
    # ===================================================
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    # ===================================================
    # Custom Accounts Authentication
    # ===================================================
    path('auth/', include('accounts.urls')),  # This adds /register/, /login/, etc
    
    # ===================================================
    # Pusher Authentication
    # ===================================================
    path('pusher/auth/', pusher_auth, name='pusher-auth'),
    
    # ===================================================
    # Feature APIs
    # ===================================================
    path('users/', include('users.urls')),
    path('tasks/', include('tasks.urls')),
    path('cards/', include('cards.urls')),
    path('compliance/', include('compliance.urls')),
    path('crypto/', include('crypto.urls')),
    path('escrow/', include('escrow.urls')),
    path('notifications/', include('notifications.urls')),
    path('payments/', include('payments.urls')),
    path('receipts/', include('receipts.urls')),
    path('transactions/', include('transactions.urls')),
    path('transfers/', include('transfers.urls')),
]