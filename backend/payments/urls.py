# payments/urls.py - CORRECTED VERSION
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Try importing webhooks, but handle if they fail
try:
    from .webhooks import stripe_webhook, paypal_webhook
    WEBHOOKS_AVAILABLE = True
except ImportError as e:
    WEBHOOKS_AVAILABLE = False

router = DefaultRouter()

# Register only views that exist
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'cards', views.CardViewSet, basename='card')
router.register(r'payment-methods', views.PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    path('', include(router.urls)),
    path('quick-transfer/', views.quick_transfer, name='quick-transfer'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('accounts/<int:pk>/balance/', views.AccountViewSet.as_view({'get': 'balance'}), name='account-balance'),
]

# Only add webhook URLs if available
if WEBHOOKS_AVAILABLE:
    urlpatterns += [
        path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
        path('webhooks/paypal/', paypal_webhook, name='paypal-webhook'),
    ]