from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CryptoAssetViewSet, CryptoWalletViewSet, CryptoTransactionViewSet,
    CryptoAddressViewSet, FiatPlatformViewSet, UserFiatAccountViewSet
)

router = DefaultRouter()
router.register(r'assets', CryptoAssetViewSet, basename='crypto-asset')
router.register(r'wallets', CryptoWalletViewSet, basename='crypto-wallet')
router.register(r'transactions', CryptoTransactionViewSet, basename='crypto-transaction')
router.register(r'addresses', CryptoAddressViewSet, basename='crypto-address')
router.register(r'fiat-platforms', FiatPlatformViewSet, basename='fiat-platform')
router.register(r'fiat-accounts', UserFiatAccountViewSet, basename='fiat-account')

urlpatterns = [
    path('', include(router.urls)),
]