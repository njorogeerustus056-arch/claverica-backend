import os

# 1. Create transactions/urls.py
transactions_urls = '''from django.urls import path
from . import views

urlpatterns = [
    path('wallet/balance/', views.get_wallet_balance_for_current_user, name='wallet_balance'),
    path('recent/', views.get_recent_transactions, name='recent_transactions'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
'''

with open('transactions/urls.py', 'w') as f:
    f.write(transactions_urls)
print("✓ Created transactions/urls.py")

# 2. Update users/views.py
users_views = '''from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Account

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user's profile"""
    user = request.user
    
    return Response({
        'full_name': f"{user.first_name} {user.last_name}".strip(),
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'account_number': user.account_number,
        'phone': user.phone,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    """Get minimal user info for authentication"""
    user = request.user
    
    return Response({
        'id': user.id,
        'email': user.email,
        'account_number': user.account_number,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })
'''

with open('users/views.py', 'w') as f:
    f.write(users_views)
print("✓ Updated users/views.py")

# 3. Update cards/urls.py
cards_urls = '''from django.urls import path
from .views import UserCardsAPIView

urlpatterns = [
    path('user-cards/', UserCardsAPIView.as_view(), name='user_cards'),
]
'''

with open('cards/urls.py', 'w') as f:
    f.write(cards_urls)
print("✓ Updated cards/urls.py")

print("\n✅ All files updated! Run:")
print("python manage.py makemigrations")
print("python manage.py migrate")
print("python manage.py runserver")