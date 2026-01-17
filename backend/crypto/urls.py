# crypto/urls.py - UPDATED TO USE CENTRAL COMPLIANCE SYSTEM

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
# REMOVED: All compliance view imports

router = DefaultRouter()
router.register(r'assets', views.CryptoAssetViewSet, basename='crypto-asset')
router.register(r'wallets', views.CryptoWalletViewSet, basename='crypto-wallet')
router.register(r'transactions', views.CryptoTransactionViewSet, basename='crypto-transaction')
router.register(r'addresses', views.CryptoAddressViewSet, basename='crypto-address')
router.register(r'fiat-platforms', views.FiatPlatformViewSet, basename='fiat-platform')
router.register(r'fiat-accounts', views.UserFiatAccountViewSet, basename='fiat-account')
router.register(r'compliance-flags', views.CryptoComplianceFlagViewSet, basename='crypto-compliance-flag')
router.register(r'audit-logs', views.CryptoAuditLogViewSet, basename='crypto-audit-log')

urlpatterns = [
    path('', include(router.urls)),
    
    # ALL COMPLIANCE ENDPOINTS REMOVED - USE CENTRAL COMPLIANCE APP
    # For crypto KYC requests:
    # POST /api/compliance/api/kyc/ (via KYCVerificationViewSet)
    # 
    # For TAC verification:
    # POST /api/compliance/api/tacs/verify/
    #
    # For compliance status:
    # GET /api/compliance/api/integration/status/{compliance_id}/
]