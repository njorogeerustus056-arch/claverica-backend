# payments/urls.py - UPDATED FOR COMPLIANCE INTEGRATION

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import compliance_views  # Updated compliance views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'cards', views.CardViewSet, basename='card')

# Wallet system routers
router.register(r'wallets/main-business', views.MainBusinessWalletViewSet, basename='main-business-wallet')
router.register(r'wallets/employee-platform', views.EmployeePlatformWalletViewSet, basename='employee-platform-wallet')
router.register(r'withdrawals', views.WithdrawalRequestViewSet, basename='withdrawal')
router.register(r'notifications', views.PaymentTransactionNotificationViewSet, basename='notification')
router.register(r'activity-feed', views.ActivityFeedViewSet, basename='activity-feed')

# Compliance endpoints - UPDATED
urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard and stats
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats-alias'),
    
    # Wallet operations
    path('pay-employee/', views.pay_employee, name='pay-employee'),
    path('schedule-agent-call/', views.schedule_agent_call, name='schedule-agent-call'),
    path('wallet-dashboard/', views.get_wallet_dashboard, name='wallet-dashboard'),
    
    # COMPLIANCE ENDPOINTS - UPDATED TO USE CENTRAL COMPLIANCE
    path('compliance/request-manual-payment/', compliance_views.request_manual_payment, name='request-manual-payment'),
    path('compliance/verify-tac/', compliance_views.verify_tac, name='verify-tac'),
    path('compliance/submit-kyc-form/', compliance_views.submit_kyc_form, name='submit-kyc-form'),
    path('compliance/user/status/', compliance_views.user_compliance_status, name='user-compliance-status'),
    
    # ADMIN COMPLIANCE ENDPOINTS - UPDATED
    path('compliance/admin/dashboard/', compliance_views.admin_compliance_dashboard, name='admin-compliance-dashboard'),
    path('compliance/admin/generate-tac/', compliance_views.admin_generate_tac, name='admin-generate-tac'),
    path('compliance/admin/schedule-video-call/', compliance_views.admin_schedule_video_call, name='admin-schedule-video-call'),
    path('compliance/admin/complete-video-call/', compliance_views.admin_complete_video_call, name='admin-complete-video-call'),
    path('compliance/admin/approve-request/', compliance_views.admin_approve_request, name='admin-approve-request'),
    path('compliance/admin/reject-request/', compliance_views.admin_reject_request, name='admin-reject-request'),
]