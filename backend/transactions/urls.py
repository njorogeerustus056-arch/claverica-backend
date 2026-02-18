from django.urls import path
from . import views

urlpatterns = [
    # Existing endpoints for frontend
    path('wallet/balance/', views.get_wallet_balance_for_current_user, name='wallet_balance'),
    path('recent/', views.get_recent_transactions, name='recent_transactions'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # ADDED: Critical endpoints for Payments/Transfers apps
    path('credit/', views.credit_wallet, name='credit-wallet'),
    path('debit/', views.debit_wallet, name='debit-wallet'),
    path('history/<str:account_number>/', views.get_transaction_history, name='transaction-history'),
    path('balance/<str:account_number>/', views.get_wallet_balance, name='wallet-balance'),
]
