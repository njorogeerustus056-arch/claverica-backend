"""
transfers/urls.py - Updated URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransferViewSet, TransferLimitViewSet, TransferSearchView

router = DefaultRouter()
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'transfer-limits', TransferLimitViewSet, basename='transfer-limit')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', TransferSearchView.as_view(), name='transfer-search'),
]