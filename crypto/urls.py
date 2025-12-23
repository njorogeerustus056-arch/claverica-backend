"""
Crypto Application URL Configuration
Handles cryptocurrency-related endpoints
"""

from django.urls import path
from . import views

app_name = 'crypto'

urlpatterns = [
    # Wallet Management
    path('wallets/', views.WalletListCreateView.as_view(), name='wallet-list-create'),
    path('wallets/<uuid:pk>/', views.WalletDetailView.as_view(), name='wallet-detail'),
    path('wallets/<uuid:pk>/balance/', views.WalletBalanceView.as_view(), name='wallet-balance'),
    path('wallets/<uuid:pk>/transactions/', views.WalletTransactionsView.as_view(), name='wallet-transactions'),
    
    # Cryptocurrency Management
    path('currencies/', views.CryptoCurrencyListView.as_view(), name='currency-list'),
    path('currencies/<str:symbol>/', views.CryptoCurrencyDetailView.as_view(), name='currency-detail'),
    path('currencies/<str:symbol>/price/', views.CryptoPriceView.as_view(), name='currency-price'),
    
    # Transactions
    path('transactions/', views.CryptoTransactionListView.as_view(), name='transaction-list'),
    path('transactions/create/', views.CryptoTransactionCreateView.as_view(), name='transaction-create'),
    path('transactions/<uuid:pk>/', views.CryptoTransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/<uuid:pk>/status/', views.TransactionStatusView.as_view(), name='transaction-status'),
    
    # Deposits
    path('deposits/', views.DepositListView.as_view(), name='deposit-list'),
    path('deposits/initiate/', views.InitiateDepositView.as_view(), name='deposit-initiate'),
    path('deposits/<uuid:pk>/', views.DepositDetailView.as_view(), name='deposit-detail'),
    path('deposits/<uuid:pk>/confirm/', views.ConfirmDepositView.as_view(), name='deposit-confirm'),
    
    # Withdrawals
    path('withdrawals/', views.WithdrawalListView.as_view(), name='withdrawal-list'),
    path('withdrawals/request/', views.RequestWithdrawalView.as_view(), name='withdrawal-request'),
    path('withdrawals/<uuid:pk>/', views.WithdrawalDetailView.as_view(), name='withdrawal-detail'),
    path('withdrawals/<uuid:pk>/cancel/', views.CancelWithdrawalView.as_view(), name='withdrawal-cancel'),
    
    # Exchange/Swap
    path('exchange/quote/', views.ExchangeQuoteView.as_view(), name='exchange-quote'),
    path('exchange/execute/', views.ExecuteExchangeView.as_view(), name='exchange-execute'),
    path('exchange/history/', views.ExchangeHistoryView.as_view(), name='exchange-history'),
    
    # Address Management
    path('addresses/', views.CryptoAddressListView.as_view(), name='address-list'),
    path('addresses/generate/', views.GenerateAddressView.as_view(), name='address-generate'),
    path('addresses/<uuid:pk>/', views.CryptoAddressDetailView.as_view(), name='address-detail'),
    path('addresses/<uuid:pk>/verify/', views.VerifyAddressView.as_view(), name='address-verify'),
    
    # Price & Market Data
    path('prices/', views.CryptoPriceListView.as_view(), name='price-list'),
    path('prices/history/', views.PriceHistoryView.as_view(), name='price-history'),
    path('market/stats/', views.MarketStatsView.as_view(), name='market-stats'),
    
    # Portfolio
    path('portfolio/', views.PortfolioView.as_view(), name='portfolio'),
    path('portfolio/performance/', views.PortfolioPerformanceView.as_view(), name='portfolio-performance'),
    path('portfolio/allocation/', views.PortfolioAllocationView.as_view(), name='portfolio-allocation'),
    
    # Gas Fees & Network
    path('network/fees/', views.NetworkFeesView.as_view(), name='network-fees'),
    path('network/status/', views.NetworkStatusView.as_view(), name='network-status'),
    
    # Webhooks (for blockchain confirmations)
    path('webhooks/deposit/', views.DepositWebhookView.as_view(), name='webhook-deposit'),
    path('webhooks/withdrawal/', views.WithdrawalWebhookView.as_view(), name='webhook-withdrawal'),
]
