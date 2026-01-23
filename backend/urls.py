from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from backend.mock_api_detailed import (
    api_root, kyc_verifications_my_status, kyc_documents_list,
    transactions_list, tac_verify, tac_generate, verify_email,
    crypto_wallets, cards_list, payments_list
)

def home(request):
    return HttpResponse('''
    <!DOCTYPE html>
    <html><head><title>🏦 Claverica Banking</title><style>
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
    background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);margin:0;padding:0;
    display:flex;justify-content:center;align-items:center;min-height:100vh;color:white;}
    .container{background:rgba(255,255,255,0.1);backdrop-filter:blur(10px);
    border-radius:20px;padding:40px;text-align:center;max-width:600px;width:90%;}
    h1{font-size:2.5rem;margin-bottom:20px;}
    .admin-link{display:inline-block;background:white;color:#667eea;
    padding:12px 24px;border-radius:50px;text-decoration:none;font-weight:bold;}
    .emoji{font-size:3rem;display:block;margin-bottom:20px;}
    </style></head>
    <body><div class="container">
        <span class="emoji">🏦</span><h1>Claverica Banking Backend</h1>
        <p>API running with detailed mock data</p>
        <a href="/admin/" class="admin-link">Admin Panel →</a>
    </div></body></html>
    ''')

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('api/auth/', include('backend.accounts.urls')),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    path('api/', api_root),
    path('api/transactions/', transactions_list),
    path('api/kyc/verifications/my_status/', kyc_verifications_my_status),
    path('api/kyc/documents/', kyc_documents_list),
    path('api/tac/verify/', tac_verify),
    path('api/tac/generate/', tac_generate),
    path('api/auth/verify-email/', verify_email),
    path('api/crypto/wallets/', crypto_wallets),
    path('api/cards/', cards_list),
    path('api/payments/', payments_list),
]

# NUCLEAR BYPASS - Add this at the end of urlpatterns
from urls_override import test_auth

urlpatterns += [
    path('api/test-auth/', test_auth, name='test-auth'),
]
