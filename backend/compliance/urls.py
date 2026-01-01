"""
compliance/urls.py - URL configuration for compliance app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'compliance'

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'kyc/verifications', views.KYCVerificationViewSet, basename='kyc-verification')
router.register(r'kyc/documents', views.KYCDocumentViewSet, basename='kyc-document')
router.register(r'withdrawals', views.WithdrawalRequestViewSet, basename='withdrawal')
router.register(r'audit-logs', views.ComplianceAuditLogViewSet, basename='audit-log')

urlpatterns = [
    # API endpoints using ViewSets
    path('api/', include(router.urls)),
    
    # TAC endpoints
    path('api/tac/generate/', views.TACCodeViewSet.as_view({'post': 'generate'}), name='tac-generate'),
    path('api/tac/verify/', views.TACCodeViewSet.as_view({'post': 'verify'}), name='tac-verify'),
    
    # Dashboard and status endpoints
    path('api/dashboard/', views.ComplianceDashboardView.as_view(), name='compliance-dashboard'),
    path('api/user-status/', views.UserComplianceStatusView.as_view(), name='user-compliance-status'),
    path('api/user-status/<str:user_id>/', views.UserComplianceStatusView.as_view(), name='user-compliance-status-detail'),
    
    # Legacy endpoints (for backward compatibility)
    path('kyc/submit/', views.submit_kyc_legacy, name='kyc_submit_legacy'),
    path('kyc/upload-document/', views.upload_kyc_document_legacy, name='upload_document_legacy'),
    path('kyc/status/<str:user_id>/', views.get_kyc_status_legacy, name='kyc_status_legacy'),
    path('tac/generate/', views.generate_tac_legacy, name='generate_tac_legacy'),
    path('tac/verify/', views.verify_tac_legacy, name='verify_tac_legacy'),
    path('withdrawal/request/', views.request_withdrawal_legacy, name='request_withdrawal_legacy'),
    path('verification/documents/<uuid:verification_id>/', views.get_verification_documents_legacy, name='verification_documents_legacy'),
    path('audit-log/<str:user_id>/', views.get_audit_log_legacy, name='audit_log_legacy'),
    
    # Additional endpoints
    path('api/kyc/status/', views.KYCVerificationViewSet.as_view({'get': 'my_status'}), name='kyc-my-status'),
    
    # Document download endpoint
    path('api/documents/<uuid:pk>/download/', views.KYCDocumentViewSet.as_view({'get': 'download'}), name='document-download'),
    
    # Withdrawal actions
    path('api/withdrawals/<uuid:pk>/verify-tac/', views.WithdrawalRequestViewSet.as_view({'post': 'verify_tac'}), name='withdrawal-verify-tac'),
    path('api/withdrawals/<uuid:pk>/cancel/', views.WithdrawalRequestViewSet.as_view({'post': 'cancel'}), name='withdrawal-cancel'),
    
    # KYC actions
    path('api/kyc/verifications/<uuid:pk>/approve/', views.KYCVerificationViewSet.as_view({'post': 'approve'}), name='kyc-approve'),
    path('api/kyc/verifications/<uuid:pk>/reject/', views.KYCVerificationViewSet.as_view({'post': 'reject'}), name='kyc-reject'),
]

# Add API documentation
urlpatterns += [
    path('api/docs/', include('rest_framework.urls', namespace='rest_framework')),
]