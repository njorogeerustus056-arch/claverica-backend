# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    index, 
    RegisterView, 
    CustomTokenObtainPairView,
    ManualLoginView  # Alternative if CustomTokenObtainPairView doesn't work
)

urlpatterns = [
    # Health check
    path('', index, name='accounts-index'),
    
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    
    # JWT Token endpoints
    # OPTION 1: Use CustomTokenObtainPairView (recommended)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # OPTION 2: If Option 1 doesn't work, comment out the line above and use this:
    # path('auth/token/', ManualLoginView.as_view(), name='token_obtain_pair'),
    
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

"""
USAGE NOTES:

1. Start with CustomTokenObtainPairView (Option 1). This integrates cleanly 
   with Simple JWT and uses your custom EmailBackend automatically.

2. If you still get "No active account found" errors, switch to ManualLoginView 
   (Option 2) which gives you complete control over the authentication process.

3. Your frontend can continue sending:
   {"username": "user@example.com", "password": "..."}
   
   Both views will handle it correctly.

4. Response format will be:
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "user": {
       "id": 1,
       "email": "user@example.com",
       "first_name": "John",
       "last_name": "Doe"
     }
   }
"""