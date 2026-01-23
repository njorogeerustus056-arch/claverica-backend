# Detailed Mock API for Claverica Banking
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import uuid

# KYC API
@api_view(['GET'])
@permission_classes([AllowAny])
def kyc_verifications_my_status(request):
    return Response({'status': 'verified', 'level': 'full'})

@api_view(['GET'])
@permission_classes([AllowAny])
def kyc_documents_list(request):
    return Response({'documents': [
        {'id': str(uuid.uuid4()), 'type': 'national_id', 'status': 'verified'},
        {'id': str(uuid.uuid4()), 'type': 'proof_of_address', 'status': 'verified'}
    ]})

# Transactions API
@api_view(['GET'])
@permission_classes([AllowAny])
def transactions_list(request):
    return Response({
        'results': [
            {'id': str(uuid.uuid4()), 'type': 'deposit', 'amount': '1500.00', 'status': 'completed'},
            {'id': str(uuid.uuid4()), 'type': 'transfer', 'amount': '250.00', 'status': 'completed'}
        ]
    })

# TAC API
@api_view(['POST'])
@permission_classes([AllowAny])
def tac_verify(request):
    return Response({'valid': True, 'message': 'Code verified'})

@api_view(['POST'])
@permission_classes([AllowAny])
def tac_generate(request):
    return Response({'code': '123456'})

# Auth API
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    return Response({'verified': True, 'email': 'user@claverica.com'})

# Crypto API
@api_view(['GET'])
@permission_classes([AllowAny])
def crypto_wallets(request):
    return Response({'wallets': [
        {'id': str(uuid.uuid4()), 'asset': 'BTC', 'balance': '0.125'},
        {'id': str(uuid.uuid4()), 'asset': 'ETH', 'balance': '2.5'}
    ]})

# Cards API
@api_view(['GET'])
@permission_classes([AllowAny])
def cards_list(request):
    return Response({'cards': [
        {'id': str(uuid.uuid4()), 'type': 'virtual', 'last_four': '4242'}
    ]})

# Payments API
@api_view(['GET'])
@permission_classes([AllowAny])
def payments_list(request):
    return Response({'payments': [
        {'id': str(uuid.uuid4()), 'amount': '99.99', 'status': 'completed'}
    ]})

# API Root
@api_view(['GET'])
@permission_classes([AllowAny])
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
            'payments': '/api/payments/'
        }
    })
# Test change
