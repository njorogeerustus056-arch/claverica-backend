# backend/views/pusher_auth.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pusher_authentication(request):
    """
    Authenticate a user for a private Pusher channel
    """
    try:
        # Import pusher here, inside the function
        import pusher
        
        # Initialize Pusher client here
        pusher_client = pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True
        )
        
        # Get the authenticated user from the JWT token
        user = request.user

        # Parse request body
        data = json.loads(request.body)
        channel_name = data.get('channel_name')
        socket_id = data.get('socket_id')

        # Validate that the user is trying to access their own channel
        expected_channel = f'private-user-{user.account_number}'

        if channel_name != expected_channel:
            return JsonResponse(
                {'error': 'Unauthorized channel access'},
                status=403
            )

        # Authenticate the user for this channel
        auth = pusher_client.authenticate(
            channel=channel_name,
            socket_id=socket_id
        )

        return JsonResponse(auth)

    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON'},
            status=400
        )
    except Exception as e:
        print(f" Pusher auth error: {e}")
        return JsonResponse(
            {'error': str(e)},
            status=500
        )