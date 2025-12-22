"""
URL configuration for Cards app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CardViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'cards', CardViewSet, basename='card')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
