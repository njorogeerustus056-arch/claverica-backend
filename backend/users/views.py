# users/views.py
import logging
import json
import random
import string
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from .models import UserProfile, UserSettings, SecurityAlert, ConnectedDevice, ActivityLog
from .serializers import UserProfileSerializer

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------
def get_avatar_initials(account):
    """Generate avatar initials from account name"""
    if account.first_name and account.last_name:
        return f"{account.first_name[0]}{account.last_name[0]}".upper()
    elif account.email:
        return account.email[:2].upper()
    return "U"


def pretty_time_ago(dt):
    """Convert datetime to "X time ago" format"""
    if not dt:
        return "Never"
        
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def create_activity_log(account, activity_type, request=None, metadata=None):
    """Create an activity log entry"""
    ip_address = None
    user_agent = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
    
    try:
        return ActivityLog.objects.create(
            account=account,
            activity_type=activity_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"Failed to create activity log: {e}")
        return None


# -----------------------------------------------------------------
# USER PROFILE VIEW
# -----------------------------------------------------------------
class UserProfileView(APIView):
    """
    GET /api/users/profile/
    Returns user profile data
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            account = request.user
            profile = account.user_profile
            
            # Get client IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')

            # Use actual account number or generate one
            account_number = profile.account_number or f"CLV{account.id:08d}"

            profile_data = {
                "id": account.id,
                "first_name": account.first_name or "User",
                "last_name": account.last_name or "",
                "email": account.email,
                "balance": 12500.00,  # Mock for now
                "account_number": account_number,
                "ip_address": ip_address,
                "email_verified": account.email_verified,
                "phone": profile.phone or "",
                "phone_verified": profile.phone_verified,
                "subscription_tier": profile.subscription_tier,
                "avatar_color": profile.avatar_color,
                "cards": []
            }

            return Response(profile_data)

        except Exception as e:
            logger.error(f"Error in UserProfileView: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# PROFILE SETTINGS
# -----------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_settings(request):
    """Get extended profile for AccountSettings page"""
    try:
        account = request.user
        profile = account.user_profile
        settings = account.user_settings
        
        # Calculate security score
        security_score = 0
        if account.email_verified:
            security_score += 25
        if profile.phone_verified:
            security_score += 25
        if settings.two_factor_enabled:
            security_score += 25
        if profile.last_password_change and profile.last_password_change > timezone.now() - timedelta(days=90):
            security_score += 25
        
        profile_data = {
            "name": f"{account.first_name or ''} {account.last_name or ''}".strip() or account.email,
            "username": account.email,
            "email": account.email,
            "email_verified": account.email_verified,
            "phone": profile.phone or "",
            "phone_verified": profile.phone_verified,
            "account_number": profile.account_number or f"CLV{account.id:08d}",
            "member_since": account.date_joined.strftime("%b %Y") if account.date_joined else "Unknown",
            "avatar": get_avatar_initials(account),
            "tier": profile.subscription_tier or "free",
            "security_score": security_score,
            "last_password_change": pretty_time_ago(profile.last_password_change),
            "avatar_color": profile.avatar_color or "#3B82F6"
        }
        
        return Response(profile_data)
    except Exception as e:
        logger.error(f"Error in get_profile_settings: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# PROFILE CREATION/UPDATE ENDPOINTS
# -----------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_or_update_profile(request):
    """Create or update user profile with validation"""
    try:
        account = request.user
        
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(account=account)
        
        # Validate data
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save validated data
        serializer.save()
        
        # Create activity log
        create_activity_log(
            account, 
            'profile_update', 
            request, 
            {'created': created}
        )
        
        logger.info(f"{'Created' if created else 'Updated'} profile for {account.email}")
        
        # Get full profile data for response
        profile.refresh_from_db()
        profile_data = {
            "id": profile.id,
            "phone": profile.phone,
            "phone_verified": profile.phone_verified,
            "document_type": profile.document_type,
            "document_number": profile.document_number,
            "street": profile.street,
            "city": profile.city,
            "state": profile.state,
            "zip_code": profile.zip_code,
            "occupation": profile.occupation,
            "employer": profile.employer,
            "income_range": profile.income_range,
            "subscription_tier": profile.subscription_tier,
            "avatar_color": profile.avatar_color,
            "account_number": profile.account_number,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
        }
        
        message = "Profile created successfully" if created else "Profile updated successfully"
        
        return Response({
            "success": True,
            "message": message,
            "profile": profile_data
        })
        
    except Exception as e:
        logger.error(f"Error in create_or_update_profile: {str(e)}")
        return Response({
            "error": "Failed to create/update profile",
            "detail": str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_partial(request):
    """Partially update user profile fields"""
    try:
        account = request.user
        profile = account.user_profile
        
        # Validate data
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                "error": "Validation failed",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save validated data
        serializer.save()
        
        # Create activity log
        create_activity_log(
            account, 
            'profile_update', 
            request, 
            {'partial_update': True}
        )
        
        logger.info(f"Updated profile for {account.email}")
        
        return Response({
            "success": True,
            "message": "Profile updated successfully"
        })
            
    except Exception as e:
        logger.error(f"Error in update_profile_partial: {str(e)}")
        return Response({
            "error": "Failed to update profile",
            "detail": str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# USER SETTINGS
# -----------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_settings(request):
    """Get account settings from database"""
    try:
        account = request.user
        settings = account.user_settings
        profile = account.user_profile
        
        settings_data = {
            "dark_mode": settings.dark_mode,
            "activity_logs_enabled": settings.activity_logs_enabled,
            "security_pin_enabled": settings.security_pin_enabled,
            "two_factor_enabled": settings.two_factor_enabled,
            "biometric_enabled": settings.biometric_enabled,
            "email_notifications": settings.email_notifications,
            "push_notifications": settings.push_notifications,
            "sms_notifications": settings.sms_notifications,
            "data_collection": settings.data_collection,
            "subscription_tier": profile.subscription_tier or "free",
            "language": settings.language or "en"
        }
        
        return Response(settings_data)
    except Exception as e:
        logger.error(f"Error in get_settings: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_settings(request):
    """Update account settings in database"""
    try:
        data = request.data
        account = request.user
        settings = account.user_settings
        
        # Define allowed fields to update
        allowed_fields = [
            'dark_mode', 'activity_logs_enabled', 'security_pin_enabled',
            'two_factor_enabled', 'biometric_enabled', 'email_notifications',
            'push_notifications', 'sms_notifications', 'data_collection', 'language'
        ]
        
        # Update only allowed fields
        updated_fields = []
        for field in allowed_fields:
            if field in data:
                # Handle boolean fields
                if field in ['dark_mode', 'activity_logs_enabled', 'security_pin_enabled',
                           'two_factor_enabled', 'biometric_enabled', 'email_notifications',
                           'push_notifications', 'sms_notifications', 'data_collection']:
                    setattr(settings, field, bool(data[field]))
                else:
                    setattr(settings, field, data[field])
                updated_fields.append(field)
        
        if updated_fields:
            settings.save()
            create_activity_log(account, 'settings_change', request, {'updated_fields': updated_fields})
            logger.info(f"Updated settings for {account.email}: {updated_fields}")
            return Response({
                "message": "Settings updated successfully",
                "updated_fields": updated_fields
            })
        
        return Response({"error": "No valid fields provided for update"}, status=400)
    except Exception as e:
        logger.error(f"Error in update_settings: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# SECURITY ENDPOINTS
# -----------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_alerts(request):
    """Get security alerts from database"""
    try:
        account = request.user
        alerts = SecurityAlert.objects.filter(account=account).order_by('-created_at')[:20]
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": pretty_time_ago(alert.created_at),
                "resolved": alert.resolved
            })
        
        return Response({"alerts": alerts_data})
    except Exception as e:
        logger.error(f"Error in get_security_alerts: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_security_alert(request):
    """Mark alert as resolved"""
    try:
        alert_id = request.data.get('alert_id')
        
        if not alert_id:
            return Response({"error": "Alert ID is required"}, status=400)
        
        alert = SecurityAlert.objects.get(id=alert_id, account=request.user)
        alert.resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        create_activity_log(request.user, 'settings_change', request, {'alert_id': alert_id, 'action': 'resolved'})
        return Response({"message": "Alert resolved successfully"})
    except SecurityAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in resolve_security_alert: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_score(request):
    """Get calculated security score"""
    try:
        account = request.user
        profile = account.user_profile
        settings = account.user_settings
        
        security_score = 0
        if account.email_verified:
            security_score += 25
        if profile.phone_verified:
            security_score += 25
        if settings.two_factor_enabled:
            security_score += 25
        if profile.last_password_change and profile.last_password_change > timezone.now() - timedelta(days=90):
            security_score += 25
        
        return Response({"security_score": security_score})
    except Exception as e:
        logger.error(f"Error in get_security_score: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# DEVICE MANAGEMENT
# -----------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_connected_devices(request):
    """Get connected devices from database"""
    try:
        account = request.user
        devices = ConnectedDevice.objects.filter(account=account).order_by('-last_active')
        
        devices_data = []
        for device in devices:
            devices_data.append({
                "id": device.id,
                "name": device.device_name or "Unknown Device",
                "type": device.device_type or "unknown",
                "last_active": pretty_time_ago(device.last_active),
                "location": device.location or "Unknown",
                "current": device.is_current,
                "os": device.os or "Unknown",
                "model": device.device_name or "Unknown",
                "connection_type": "wifi",
                "battery_level": 100
            })
        
        return Response({"devices": devices_data})
    except Exception as e:
        logger.error(f"Error in get_connected_devices: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_device(request):
    """Disconnect device"""
    try:
        device_id = request.data.get('device_id')
        
        if not device_id:
            return Response({"error": "Device ID is required"}, status=400)
        
        device = ConnectedDevice.objects.get(id=device_id, account=request.user)
        device.delete()
        
        create_activity_log(request.user, 'device_removed', request, {'device_id': device_id})
        return Response({"message": "Device disconnected successfully"})
    except ConnectedDevice.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in disconnect_device: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# ACTIVITY LOGS
# -----------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_logs(request):
    """Get activity logs from database"""
    try:
        account = request.user
        logs = ActivityLog.objects.filter(account=account).order_by('-created_at')[:50]
        
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": log.id,
                "device": "Unknown",
                "browser": (log.user_agent or "Unknown")[:50],
                "ip": log.ip_address or "Unknown",
                "location": log.location or "Unknown",
                "country": "ke",
                "time": pretty_time_ago(log.created_at),
                "current": False,
                "status": "success",
                "activity_type": log.activity_type or "unknown"
            })
        
        return Response({"logs": logs_data})
    except Exception as e:
        logger.error(f"Error in get_activity_logs: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# DATA EXPORT
# -----------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_user_data(request):
    """Export account data"""
    try:
        account = request.user
        profile = account.user_profile
        settings = account.user_settings
        
        # Gather data from all models
        data = {
            "profile": {
                "email": account.email,
                "first_name": account.first_name or "",
                "last_name": account.last_name or "",
                "phone": profile.phone or "",
                "date_joined": account.date_joined.isoformat() if account.date_joined else None,
                "last_login": account.last_login.isoformat() if account.last_login else None
            },
            "extended_profile": {
                "phone_verified": profile.phone_verified,
                "email_verified": account.email_verified,
                "subscription_tier": profile.subscription_tier or "free",
                "account_number": profile.account_number or f"CLV{account.id:08d}",
                "last_password_change": profile.last_password_change.isoformat() if profile.last_password_change else None
            },
            "settings": {
                "dark_mode": settings.dark_mode,
                "language": settings.language or "en",
                "email_notifications": settings.email_notifications,
                "two_factor_enabled": settings.two_factor_enabled,
                "data_collection": settings.data_collection
            },
            "activity_logs_count": ActivityLog.objects.filter(account=account).count(),
            "security_alerts_count": SecurityAlert.objects.filter(account=account).count(),
            "devices_count": ConnectedDevice.objects.filter(account=account).count(),
            "exported_at": timezone.now().isoformat()
        }
        
        create_activity_log(account, 'settings_change', request, {'action': 'data_export'})
        
        return Response({
            "data": data,
            "filename": f"claverica_export_{account.email}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json",
            "message": "Data exported successfully"
        })
    except Exception as e:
        logger.error(f"Error in export_user_data: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# PASSWORD MANAGEMENT (MOVED TO users app)
# -----------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password"""
    try:
        data = request.data
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate
        if not all([old_password, new_password, confirm_password]):
            return Response({"error": "All fields are required"}, status=400)
        
        if new_password != confirm_password:
            return Response({"error": "New passwords do not match"}, status=400)
        
        if len(new_password) < 8:
            return Response({"error": "Password must be at least 8 characters"}, status=400)
        
        # Check old password
        account = request.user
        if not account.check_password(old_password):
            return Response({"error": "Current password is incorrect"}, status=400)
        
        # Update password
        account.set_password(new_password)
        account.save()
        
        # Update last_password_change in profile
        profile = account.user_profile
        profile.last_password_change = timezone.now()
        profile.save()
        
        # Create security alert
        SecurityAlert.objects.create(
            account=account,
            alert_type='password_change',
            severity='medium',
            message='Password was changed successfully',
            metadata={'changed_at': timezone.now().isoformat()}
        )
        
        create_activity_log(account, 'password_change', request)
        
        # Keep account logged in
        update_session_auth_hash(request, account)
        
        return Response({"message": "Password changed successfully"})
    except Exception as e:
        logger.error(f"Error in change_password: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# VERIFICATION ENDPOINTS
# -----------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email(request):
    """Send email verification"""
    try:
        account = request.user
        profile = account.user_profile
        
        # Generate verification code (in production, store in database)
        code = ''.join(random.choices(string.digits, k=6))
        
        # In production, send actual email
        logger.info(f"Email verification code for {account.email}: {code}")
        
        # For now, just mark as verified for demo
        account.email_verified = True
        account.save()
        
        create_activity_log(account, 'email_verification', request)
        
        return Response({
            "message": "Email verification sent. Check your email for the verification code."
        })
    except Exception as e:
        logger.error(f"Error in verify_email: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    """Send phone verification"""
    try:
        account = request.user
        profile = account.user_profile
        
        phone_number = request.data.get('phone')
        if phone_number:
            profile.phone = phone_number
            profile.save()
        
        # Generate verification code (in production, store in database)
        code = ''.join(random.choices(string.digits, k=6))
        
        # In production, send actual SMS
        logger.info(f"Phone verification code for {profile.phone or 'no phone'}: {code}")
        
        # For now, just return success for demo
        create_activity_log(account, 'phone_verification', request)
        
        return Response({
            "message": "SMS verification sent to your phone number.",
            "requires_code": True
        })
    except Exception as e:
        logger.error(f"Error in verify_phone: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_phone_verification(request):
    """Confirm phone verification with code"""
    try:
        code = request.data.get('code')
        
        if not code or len(code) != 6 or not code.isdigit():
            return Response({"error": "Invalid verification code"}, status=400)
        
        # In production, verify the code against database
        account = request.user
        profile = account.user_profile
        profile.phone_verified = True
        profile.save()
        
        return Response({"message": "Phone verified successfully"})
    except Exception as e:
        logger.error(f"Error in confirm_phone_verification: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)