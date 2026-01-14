# crypto/urls.py - UPDATED WITH COMPLIANCE ROUTES

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views.compliance_views import (
    request_crypto_kyc_view,
    verify_crypto_tac_view,
    crypto_compliance_status_view,
    flag_suspicious_crypto_view,
    schedule_video_verification_view,
    get_crypto_compliance_dashboard,
    admin_approve_crypto_request,
    admin_reject_crypto_request
)

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
    
    # COMPLIANCE ENDPOINTS
    path('compliance/request-kyc/', request_crypto_kyc_view, name='crypto-request-kyc'),
    path('compliance/verify-tac/', verify_crypto_tac_view, name='crypto-verify-tac'),
    path('compliance/status/<uuid:transaction_id>/', crypto_compliance_status_view, name='crypto-compliance-status'),
    path('compliance/dashboard/', get_crypto_compliance_dashboard, name='crypto-compliance-dashboard'),
    
    # ADMIN COMPLIANCE ENDPOINTS
    path('compliance/admin/flag-suspicious/', flag_suspicious_crypto_view, name='flag-suspicious-crypto'),
    path('compliance/admin/schedule-video/', schedule_video_verification_view, name='schedule-video-verification'),
    path('compliance/admin/approve/', admin_approve_crypto_request, name='admin-approve-crypto-request'),
    path('compliance/admin/reject/', admin_reject_crypto_request, name='admin-reject-crypto-request'),
]