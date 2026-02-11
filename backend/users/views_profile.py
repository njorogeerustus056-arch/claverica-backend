from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_account_settings(request):
    user = request.user
    return Response({
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'two_factor_enabled': getattr(user, 'two_factor_enabled', False),
        'notification_preferences': {
            'email': True,
            'sms': False,
            'push': True,
        }
    })

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_settings(request):
    return Response({'status': 'settings updated'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_connected_devices(request):
    return Response({'devices': []})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_device(request, device_id):
    return Response({'status': 'device removed'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_logs(request):
    return Response({'logs': []})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    return Response({'status': 'password changed'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email(request):
    return Response({'status': 'email verified'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    return Response({'status': 'phone verified'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_two_factor(request):
    return Response({'status': '2FA setup'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    return Response({'data': {}})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    return Response({'status': 'account deleted'})
