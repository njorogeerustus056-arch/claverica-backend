"""
compliance/urls.py - URL routing for compliance endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .views import (
    TransferViewSet, AdminTransferViewSet,
    ComplianceSettingViewSet, check_kyc_requirement
)

# Create routers
router = DefaultRouter()
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'admin/transfers', AdminTransferViewSet, basename='admin-transfer')
router.register(r'admin/settings', ComplianceSettingViewSet, basename='compliance-setting')

#  ADD THIS: Root endpoint for /api/compliance/
@api_view(['GET'])
def compliance_root(request):
    return Response({
        'message': 'Compliance API',
        'endpoints': {
            'transfers': '/api/compliance/transfers/',
            'transfer_status': '/api/compliance/transfers/{id}/status/',
            'verify_tac': '/api/compliance/transfers/{id}/verify-tac/',
            'check_kyc': '/api/compliance/check-kyc/',
            'admin_transfers': '/api/compliance/admin/transfers/',
        }
    })

urlpatterns = [
    path('', compliance_root, name='api-root'),  #  ADD THIS LINE
    path('', include(router.urls)),
    path('check-kyc/', check_kyc_requirement, name='check-kyc'),
    
    #  ADD THIS: Custom route for verify-tac (hyphenated)
    path('transfers/<int:pk>/verify-tac/', 
         TransferViewSet.as_view({'post': 'verify_tac'}), 
         name='transfer-verify-tac'),
]

# API URL patterns
api_urlpatterns = [
    path('', include(urlpatterns)),
]