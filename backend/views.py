"""
Backend Gateway Views
Health check and API root endpoints
"""

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and deployment verification.
    Returns system status including database connectivity.
    
    Used by:
    - Render.com health checks
    - Load balancers
    - Monitoring services
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
