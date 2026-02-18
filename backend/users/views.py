# users/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Account

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get complete user profile data"""
    user = request.user
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': f"{user.first_name} {user.last_name}".strip(),
        'account_number': user.account_number,
        'phone': user.phone,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
        'date_of_birth': user.date_of_birth,
        'gender': user.gender,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'kyc_status': user.kyc_status,
        'risk_level': user.risk_level,
        'account_status': user.account_status,
        'occupation': user.occupation,
        'employer': user.employer,
        'income_range': user.income_range,
        'address_line1': user.address_line1,
        'address_line2': user.address_line2,
        'city': user.city,
        'state_province': user.state_province,
        'postal_code': user.postal_code,
        'country': user.country,
        'nationality': user.nationality,
        'country_of_residence': user.country_of_residence,
        'doc_type': user.doc_type,
        'doc_number': user.doc_number,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    """Get basic user info for auth verification"""
    user = request.user
    return Response({
        'id': user.id,
        'email': user.email,
        'account_number': user.account_number,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
    })
