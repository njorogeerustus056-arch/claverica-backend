"""
Custom Middleware for Claverica Backend
Request logging, security, and monitoring
"""

import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses.
    Useful for debugging, monitoring, and audit trails.
    """
    
    def process_request(self, request):
        """Log incoming request details."""
        request.start_time = time.time()
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        request.client_ip = ip
        
        # Log request
        log_data = {
            'method': request.method,
            'path': request.path,
            'ip': ip,
            'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }
        
        logger.info(f"Request: {json.dumps(log_data)}")
        
        return None
    
    def process_response(self, request, response):
        """Log response details."""
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log response
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'ip': getattr(request, 'client_ip', 'Unknown'),
                'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            }
            
            # Use different log levels based on status code
            if response.status_code >= 500:
                logger.error(f"Response: {json.dumps(log_data)}")
            elif response.status_code >= 400:
                logger.warning(f"Response: {json.dumps(log_data)}")
            else:
                logger.info(f"Response: {json.dumps(log_data)}")
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds security headers to all responses.
    Implements best practices for fintech applications.
    """
    
    def process_response(self, request, response):
        """Add security headers."""
        # Prevent clickjacking
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        if 'X-XSS-Protection' not in response:
            response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (adjust as needed)
        if 'Content-Security-Policy' not in response and not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        
        # Feature Policy / Permissions Policy
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = (
                'geolocation=(), '
                'microphone=(), '
                'camera=(), '
                'payment=(self)'
            )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware.
    For production, consider using django-ratelimit or Redis-based solution.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_storage = {}  # In production, use Redis
    
    def __call__(self, request):
        # Skip rate limiting for health check and admin
        if request.path in ['/health/', '/admin/']:
            return self.get_response(request)
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Simple rate limiting (100 requests per minute per IP)
        # In production, implement proper sliding window algorithm
        current_minute = int(time.time() // 60)
        key = f"{ip}:{current_minute}"
        
        if key not in self.rate_limit_storage:
            self.rate_limit_storage[key] = 0
        
        self.rate_limit_storage[key] += 1
        
        # Clean old entries (basic cleanup)
        old_keys = [k for k in self.rate_limit_storage.keys() 
                   if int(k.split(':')[1]) < current_minute - 5]
        for old_key in old_keys:
            del self.rate_limit_storage[old_key]
        
        # Check rate limit
        if self.rate_limit_storage[key] > 100:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.'
                },
                status=429
            )
        
        response = self.get_response(request)
        
        # Add rate limit headers
        response['X-RateLimit-Limit'] = '100'
        response['X-RateLimit-Remaining'] = str(100 - self.rate_limit_storage[key])
        
        return response


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Middleware to enable maintenance mode.
    Set MAINTENANCE_MODE=True in environment to activate.
    """
    
    def process_request(self, request):
        """Check if maintenance mode is enabled."""
        # Skip for admin and health check
        if request.path.startswith('/admin/') or request.path == '/health/':
            return None
        
        # Check maintenance mode
        maintenance_mode = settings.get('MAINTENANCE_MODE', False)
        
        if maintenance_mode:
            return JsonResponse(
                {
                    'status': 'maintenance',
                    'message': 'The API is currently under maintenance. Please try again later.',
                },
                status=503
            )
        
        return None


class APIVersionMiddleware(MiddlewareMixin):
    """
    Adds API version information to response headers.
    Useful for API versioning and client compatibility checks.
    """
    
    def process_response(self, request, response):
        """Add API version header."""
        response['X-API-Version'] = settings.API_VERSION
        return response
