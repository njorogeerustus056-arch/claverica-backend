"""
payments/urls.py - URL routing for payments
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentCodeViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'payment-codes', PaymentCodeViewSet, basename='payment-code')

urlpatterns = [
    path('', include(router.urls)),
]
