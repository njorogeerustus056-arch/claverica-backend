"""
compliance/urls.py - URL configuration for central compliance app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'compliance'

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'requests', views.ComplianceRequestViewSet, basename='compliance-request')
router.register(r'kyc', views.KYCVerificationViewSet, basename='kyc-verification')
router.register(r'documents', views.KYCDocumentViewSet, basename='kyc-document')
router.register(r'tacs', views.TACRequestViewSet, basename='tac-request')
router.register(r'video-calls', views.VideoCallSessionViewSet, basename='video-call')
router.register(r'audit-logs', views.ComplianceAuditLogViewSet, basename='audit-log')
router.register(r'rules', views.ComplianceRuleViewSet, basename='compliance-rule')
router.register(r'alerts', views.ComplianceAlertViewSet, basename='compliance-alert')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Dashboard and overview
    path('api/dashboard/', views.ComplianceDashboardView.as_view(), name='compliance-dashboard'),
    path('api/search/', views.ComplianceSearchView.as_view(), name='compliance-search'),
    path('api/health/', views.health_check, name='health-check'),
    
    # Integration endpoints for other apps
    path('api/integration/create-request/', views.create_compliance_request, name='create-compliance-request'),
    path('api/integration/status/<str:compliance_id>/', views.check_compliance_status, name='check-compliance-status'),
    path('api/integration/generate-tac/<str:compliance_id>/', views.generate_tac_for_request, name='generate-tac-for-request'),
    path('api/integration/verify-tac/<str:compliance_id>/', views.verify_tac_for_request, name='verify-tac-for-request'),
    
    # Additional endpoints
    path('api/kyc/<str:kyc_id>/documents/', views.KYCVerificationViewSet.as_view({'get': 'documents'}), name='kyc-documents'),
    path('api/kyc/status/', views.KYCVerificationViewSet.as_view({'get': 'status'}), name='kyc-status'),
    path('api/requests/<str:compliance_id>/approve/', views.ComplianceRequestViewSet.as_view({'post': 'approve'}), name='approve-request'),
    path('api/requests/<str:compliance_id>/reject/', views.ComplianceRequestViewSet.as_view({'post': 'reject'}), name='reject-request'),
    path('api/requests/<str:compliance_id>/escalate/', views.ComplianceRequestViewSet.as_view({'post': 'escalate'}), name='escalate-request'),
    path('api/requests/<str:compliance_id>/assign/', views.ComplianceRequestViewSet.as_view({'post': 'assign'}), name='assign-request'),
    path('api/requests/<str:compliance_id>/request-info/', views.ComplianceRequestViewSet.as_view({'post': 'request_info'}), name='request-info'),
    path('api/kyc/<str:kyc_id>/approve/', views.KYCVerificationViewSet.as_view({'post': 'approve'}), name='approve-kyc'),
    path('api/kyc/<str:kyc_id>/reject/', views.KYCVerificationViewSet.as_view({'post': 'reject'}), name='reject-kyc'),
    path('api/documents/<str:document_id>/verify/', views.KYCDocumentViewSet.as_view({'post': 'verify'}), name='verify-document'),
    path('api/documents/<str:document_id>/download/', views.KYCDocumentViewSet.as_view({'get': 'download'}), name='download-document'),
    path('api/tacs/generate/', views.TACRequestViewSet.as_view({'post': 'generate'}), name='generate-tac'),
    path('api/tacs/verify/', views.TACRequestViewSet.as_view({'post': 'verify'}), name='verify-tac'),
    path('api/video-calls/schedule/', views.VideoCallSessionViewSet.as_view({'post': 'schedule'}), name='schedule-video-call'),
    path('api/video-calls/<str:session_id>/start/', views.VideoCallSessionViewSet.as_view({'post': 'start'}), name='start-video-call'),
    path('api/video-calls/<str:session_id>/complete/', views.VideoCallSessionViewSet.as_view({'post': 'complete'}), name='complete-video-call'),
    path('api/video-calls/<str:session_id>/reschedule/', views.VideoCallSessionViewSet.as_view({'post': 'reschedule'}), name='reschedule-video-call'),
    path('api/video-calls/<str:session_id>/cancel/', views.VideoCallSessionViewSet.as_view({'post': 'cancel'}), name='cancel-video-call'),
    path('api/alerts/<str:alert_id>/acknowledge/', views.ComplianceAlertViewSet.as_view({'post': 'acknowledge'}), name='acknowledge-alert'),
    path('api/alerts/<str:alert_id>/resolve/', views.ComplianceAlertViewSet.as_view({'post': 'resolve'}), name='resolve-alert'),
    path('api/alerts/unresolved-count/', views.ComplianceAlertViewSet.as_view({'get': 'unresolved_count'}), name='unresolved-alert-count'),
    path('api/rules/<str:rule_id>/activate/', views.ComplianceRuleViewSet.as_view({'post': 'activate'}), name='activate-rule'),
    path('api/rules/<str:rule_id>/deactivate/', views.ComplianceRuleViewSet.as_view({'post': 'deactivate'}), name='deactivate-rule'),
    path('api/rules/evaluate/', views.ComplianceRuleViewSet.as_view({'get': 'evaluate'}), name='evaluate-rules'),
    path('api/requests/bulk-action/', views.ComplianceRequestViewSet.as_view({'post': 'bulk_action'}), name='bulk-action'),
    path('api/requests/search/', views.ComplianceRequestViewSet.as_view({'get': 'search'}), name='search-requests'),
    
    # Legacy endpoints (for backward compatibility with other apps)
    path('api/legacy/create/', views.create_compliance_request, name='legacy-create'),
    path('api/legacy/status/<str:compliance_id>/', views.check_compliance_status, name='legacy-status'),
    
    # Webhook endpoints (for external services)
    path('api/webhooks/kyc-callback/', views.KYCVerificationViewSet.as_view({'post': 'create'}), name='kyc-webhook'),
    path('api/webhooks/sanctions-check/', views.ComplianceRequestViewSet.as_view({'post': 'create'}), name='sanctions-webhook'),
    
    # Public endpoints (no authentication required for some operations)
    path('api/public/health/', views.health_check, name='public-health-check'),
]

# Add API documentation
urlpatterns += [
    path('api/docs/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/schema/', include('drf_spectacular.urls'), name='schema'),
]