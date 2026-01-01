from django.urls import path, include 
from rest_framework.routers import DefaultRouter 
from .views import CardViewSet, TransactionViewSet, UserCardsAPIView, CardBalanceAPIView 
 
router = DefaultRouter() 
router.register(r'cards', CardViewSet, basename='card') 
router.register(r'transactions', TransactionViewSet, basename='transaction') 
 
urlpatterns = [ 
    # These paths are already under /api/cards/ from api_urls.py 
    path('', include(router.urls)),  # NO /api/ prefix 
    path('user-cards/', UserCardsAPIView.as_view(), name='user-cards'), 
] 
