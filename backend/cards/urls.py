"""
URL configuration for Cards app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CardViewSet, CardTransactionViewSet, UserCardsAPIView, CardBalanceAPIView

router = DefaultRouter()
router.register(r'cards', CardViewSet, basename='card')
router.register(r'transactions', CardTransactionViewSet, basename='cardtransaction')

urlpatterns = [
    path('', include(router.urls)),
    path('user-cards/', UserCardsAPIView.as_view(), name='user-cards'),
    path('<int:card_id>/balance/', CardBalanceAPIView.as_view(), name='card-balance'),
]