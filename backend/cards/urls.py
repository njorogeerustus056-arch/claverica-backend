# backend/cards/urls.py - CORRECTED WITH CARD TRANSACTIONS
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CardViewSet, CardTransactionViewSet  # ADD CardTransactionViewSet
from .views import user_cards_simple

router = DefaultRouter()
router.register(r'', CardViewSet, basename='card')
router.register(r'transactions', CardTransactionViewSet, basename='card-transaction')  # ADD THIS LINE

urlpatterns = [
    path('user-cards/', user_cards_simple, name='user_cards'),
    path('', include(router.urls)),
]