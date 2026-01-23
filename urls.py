from django.contrib import admin
from django.urls import path
from rest_framework.response import Response
from backend.mock_api_detailed import (
    kyc_verifications_my_status,
    kyc_documents_list,
    transactions_list,
    tac_verify,
    tac_generate,
    verify_email,
    crypto_wallets_list,
    cards_list,
    payments_list,
    mock_token_auth
)

def api_root(request):
    return Response({
        'api': 'Claverica Banking API',
        'status': 'operational',
        'endpoints': {
            'auth': '/api/token/',
            'transactions': '/api/transactions/',
            'kyc': '/api/kyc/verifications/my_status/',
            'tac': '/api/tac/verify/',
            'crypto': '/api/crypto/wallets/',
            'cards': '/api/cards/',
            'payments': '/api/payments/',
            'documents': '/api/kyc/documents/',
            'email_verify': '/api/auth/verify-email/',
            'generate_tac': '/api/tac/generate/'
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root),
    path('api/kyc/verifications/my_status/', kyc_verifications_my_status),
    path('api/kyc/documents/', kyc_documents_list),
    path('api/transactions/', transactions_list),
    path('api/tac/verify/', tac_verify),
    path('api/tac/generate/', tac_generate),
    path('api/auth/verify-email/', verify_email),
    path('api/crypto/wallets/', crypto_wallets_list),
    path('api/cards/', cards_list),
    path('api/payments/', payments_list),
    
    # OVERRIDE ALL TOKEN PATHS WITH MOCK
    path('api/token/', mock_token_auth),
    path('auth/token/', mock_token_auth),
    path('token/', mock_token_auth),
    path('api/auth/token/', mock_token_auth),
    path('rest-auth/token/', mock_token_auth),
    path('dj-rest-auth/token/', mock_token_auth),
]
path('api/test-auth/', test_auth),
