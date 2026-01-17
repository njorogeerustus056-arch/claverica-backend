# payments/urls.py - UPDATED TO USE CENTRAL COMPLIANCE SYSTEM

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
# REMOVED: from . import compliance_views  # No longer needed

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

# COMPLIANCE ENDPOINTS REMOVED - USE CENTRAL COMPLIANCE APP INSTEAD
urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard and stats
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats-alias'),
    
    # Wallet operations
    path('pay-employee/', views.pay_employee, name='pay-employee'),
    path('schedule-agent-call/', views.schedule_agent_call, name='schedule-agent-call'),
    path('wallet-dashboard/', views.get_wallet_dashboard, name='wallet-dashboard'),
    
    # ALL COMPLIANCE ENDPOINTS REMOVED - USE CENTRAL COMPLIANCE AT /api/compliance/
    # Example: To create a compliance request for a payment:
    # POST /api/compliance/api/integration/create-request/
]