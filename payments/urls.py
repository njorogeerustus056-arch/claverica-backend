from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'cards', views.CardViewSet, basename='card')
router.register(r'beneficiaries', views.BeneficiaryViewSet, basename='beneficiary')
router.register(r'savings-goals', views.SavingsGoalViewSet, basename='savings-goal')
router.register(r'crypto-wallets', views.CryptoWalletViewSet, basename='crypto-wallet')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('quick-transfer/', views.quick_transfer, name='quick-transfer'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
]
