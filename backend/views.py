"""
Backend Gateway Views
Pusher authentication endpoint
"""
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import logging
import json
import pusher
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# PUSHER AUTHENTICATION ENDPOINT - PRODUCTION READY
# ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def pusher_auth(request):
    """
    Pusher authentication endpoint for private channels.
    Required for frontend PusherClient to subscribe to private-user-* channels.
    """
    try:
        content_type = request.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            data = json.loads(request.body.decode('utf-8'))
        elif 'application/x-www-form-urlencoded' in content_type:
            parsed_data = parse_qs(request.body.decode('utf-8'))
            data = {k: v[0] for k, v in parsed_data.items()}
        else:
            return JsonResponse({'error': f'Unsupported Content-Type: {content_type}'}, status=415)
        
        socket_id = data.get('socket_id')
        channel_name = data.get('channel_name')
        
    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        return JsonResponse({'error': 'Invalid request format'}, status=400)
    
    if not socket_id or not channel_name:
        return JsonResponse({'error': 'Missing socket_id or channel_name'}, status=400)
    
    user = request.user
    
    # Validate channel name format
    if not channel_name.startswith('private-user-'):
        return JsonResponse({'error': 'Invalid channel name format'}, status=403)
    
    # Extract user ID from channel name and verify it matches authenticated user
    try:
        channel_user_id = channel_name.replace('private-user-', '')
        if str(user.id) != channel_user_id:
            logger.warning(f"User {user.id} attempted to access channel for user {channel_user_id}")
            return JsonResponse({'error': 'Unauthorized channel access'}, status=403)
    except Exception as e:
        logger.error(f"Error validating channel: {e}")
        return JsonResponse({'error': 'Invalid channel'}, status=400)
    
    try:
        pusher_client = pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            cluster=settings.PUSHER_CLUSTER,
            ssl=True,
            timeout=30
        )
        
        auth_response = pusher_client.authenticate(
            channel=channel_name,
            socket_id=socket_id
        )
        
        logger.info(f"Pusher auth successful for user {user.id}")
        return JsonResponse(auth_response)
        
    except Exception as e:
        logger.error(f"Pusher authentication failed: {e}", exc_info=True)
        return JsonResponse({'error': f'Authentication failed: {str(e)}'}, status=500)