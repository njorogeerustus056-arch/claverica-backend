"""
kyc/urls.py - CORRECTED VERSION (Removed duplicate 'api/' prefix)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    submit_documents, kyc_status, check_kyc_requirement,
    admin_dashboard, admin_review_document, test_api_page,
    # New DRF views
    KYCDocumentViewSet, KYCRequirementAPIView, AdminKYCViewSet,
    api_kyc_status
)

# Create DRF router
router = DefaultRouter()
#  FIXED: Removed 'api/' prefix to avoid double 'api/' in URL
router.register(r'documents', KYCDocumentViewSet, basename='kyc-document')           #  CHANGED
router.register(r'admin/documents', AdminKYCViewSet, basename='admin-kyc-document')  #  CHANGED

urlpatterns = [
    # HTML Pages (keep existing)
    path('submit/', submit_documents, name='kyc_submit'),
    path('status/', kyc_status, name='kyc_status'),
    path('check-requirement/', check_kyc_requirement, name='check_kyc_requirement'),
    path('test-api/', test_api_page, name='test_api_page'),

    # Admin HTML Pages (keep existing)
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/review/<uuid:document_id>/', admin_review_document, name='admin_review_document'),

    #  API Endpoints - NOW WITH CORRECT URL PATHS
    path('', include(router.urls)),
    path('check-requirement/', KYCRequirementAPIView.as_view(), name='api_check_kyc_requirement'),  #  CHANGED
    path('simple-status/', api_kyc_status, name='api_kyc_status'),                                   #  CHANGED
]
