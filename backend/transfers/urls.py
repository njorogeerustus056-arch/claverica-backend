"""
Transfer URLs - URL routing for transfer endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TransferViewSet, AdminTransferViewSet,
    TransferLimitViewSet, TransferLogViewSet
)

# Create routers
router = DefaultRouter()
router.register(r'', TransferViewSet, basename='transfer')  # CHANGED: from 'transfers' to ''
router.register(r'admin/transfers', AdminTransferViewSet, basename='admin-transfer')
router.register(r'admin/limits', TransferLimitViewSet, basename='transfer-limit')
router.register(r'admin/logs', TransferLogViewSet, basename='transfer-log')

urlpatterns = [
    path('', include(router.urls)),
]