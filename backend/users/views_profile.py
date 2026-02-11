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
