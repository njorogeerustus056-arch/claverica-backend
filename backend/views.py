"""
Backend Gateway Views
Health check and API root endpoints
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import json
import pusher
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and deployment verification.
    Returns system status including database connectivity.
    """
    health_status = {
        'status': 'healthy',
        'service': 'Claverica API',
        'version': settings.API_VERSION,
        'debug': settings.DEBUG,
    }
  
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = 'disconnected'
        health_status['error'] = str(e)
        logger.error(f"Database health check failed: {e}")
        return JsonResponse(health_status, status=503)
  
    # Check cache connectivity (if using Redis)
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        health_status['cache'] = 'connected' if cache_value == 'ok' else 'disconnected'
    except Exception as e:
        health_status['cache'] = 'disconnected'
        logger.warning(f"Cache health check failed: {e}")
  
    return JsonResponse(health_status, status=200)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    API Root endpoint.
    Provides an overview of all available API endpoints.
    """
    api_info = {
        'message': 'Welcome to Claverica API',
        'version': settings.API_VERSION,
        'documentation': '/api/docs/' if not settings.DEBUG else None,
        'endpoints': {
            'authentication': {
                'login': '/api/auth/token/',
                'refresh': '/api/auth/token/refresh/',
                'verify': '/api/auth/token/verify/',
                'logout': '/api/auth/token/blacklist/',
            },
            'features': {
                'tasks': '/api/tasks/',
                'accounts': '/api/accounts/',
                'cards': '/api/cards/',
                'compliance': '/api/compliance/',
                'crypto': '/api/crypto/',
                'escrow': '/api/escrow/',
                'notifications': '/api/notifications/',
                'payments': '/api/payments/',
                'receipts': '/api/receipts/',
                'transactions': '/api/transactions/',
            },
            'admin': '/admin/',
            'health': '/health/',
        }
    }
  
    return Response(api_info, status=status.HTTP_200_OK)

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