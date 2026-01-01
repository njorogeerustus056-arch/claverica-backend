"""
Custom Authentication Classes
Additional authentication mechanisms for Claverica API
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Extended JWT Authentication with additional security checks.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        Adds additional security validations.
        """
        result = super().authenticate(request)
        
        if result is None:
            return None
        
        user, validated_token = result
        
        # Additional security checks
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.username}")
            raise exceptions.AuthenticationFailed('User account is disabled.')
        
        # Check if user account is locked (if you have such a field)
        # if hasattr(user, 'is_locked') and user.is_locked:
        #     raise exceptions.AuthenticationFailed('Account is locked.')
        
        # Log successful authentication (for audit trail)
        logger.info(f"User authenticated: {user.username} from IP: {self.get_client_ip(request)}")
        
        return user, validated_token
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication for service-to-service communication.
    Useful for webhooks, background jobs, and third-party integrations.
    
    Usage:
        Add header: X-API-Key: your-api-key-here
    """
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return None
        
        # Validate API key
        # In production, store API keys securely (hashed) in database
        # For now, using environment variable as example
        from django.conf import settings
        valid_api_keys = getattr(settings, 'VALID_API_KEYS', [])
        
        if api_key not in valid_api_keys:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
            raise exceptions.AuthenticationFailed('Invalid API key.')
        
        # Return a system user or None for service accounts
        # You might want to create a specific "service" user
        try:
            service_user = User.objects.get(username='service_account')
            logger.info(f"Service account authenticated from IP: {self.get_client_ip(request)}")
            return (service_user, None)
        except User.DoesNotExist:
            logger.error("Service account user not found")
            raise exceptions.AuthenticationFailed('Service account not configured.')
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DeviceTokenAuthentication(BaseAuthentication):
    """
    Device-based authentication for mobile apps.
    Combines JWT with device token validation.
    
    Usage:
        Add header: X-Device-Token: device-token-here
        Along with standard JWT Bearer token
    """
    
    def authenticate(self, request):
        device_token = request.META.get('HTTP_X_DEVICE_TOKEN')
        
        if not device_token:
            return None
        
        # First, authenticate with JWT
        jwt_auth = JWTAuthentication()
        jwt_result = jwt_auth.authenticate(request)
        
        if jwt_result is None:
            return None
        
        user, validated_token = jwt_result
        
        # Validate device token
        try:
            from notifications.models import NotificationDevice
            device = NotificationDevice.objects.get(
                user=user,
                device_token=device_token,
                is_active=True
            )
            
            # Update last used timestamp
            from django.utils import timezone
            device.last_used_at = timezone.now()
            device.save(update_fields=['last_used_at'])
            
            logger.info(f"Device authenticated: {user.username} - {device.device_name}")
            return (user, validated_token)
            
        except Exception as e:
            logger.warning(f"Device token validation failed: {str(e)}")
            raise exceptions.AuthenticationFailed('Invalid or inactive device token.')