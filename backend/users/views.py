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
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, UserSettings, SecurityAlert, ConnectedDevice, ActivityLog

User = get_user_model()
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------

def get_avatar_initials(user):
    """Generate avatar initials from user name"""
    if user.first_name and user.last_name:
        return f"{user.first_name[0]}{user.last_name[0]}".upper()
    elif user.username:
        return user.username[:2].upper()
    return "U"

def pretty_time_ago(dt):
    """Convert datetime to "X time ago" format"""
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

def create_activity_log(user, activity_type, request=None, metadata=None):
    """Create an activity log entry"""
    ip_address = None
    user_agent = None
    location = None
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return ActivityLog.objects.create(
        user=user,
        activity_type=activity_type,
        ip_address=ip_address,
        user_agent=user_agent,
        location=location,
        metadata=metadata or {}
    )

# -----------------------------------------------------------------
# EXISTING CODE
# -----------------------------------------------------------------
class UserProfileView(APIView):
    """
    GET /api/users/profile/?user_id=7
    Returns user profile data including name, balance, account number, IP, etc.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.query_params.get('user_id')

        # Security check: user can only access their own profile
        if not user_id or int(user_id) != request.user.id:
            return Response(
                {"error": "You can only view your own profile"},
                status=403
            )

        try:
            user = User.objects.get(id=user_id)
            profile = user.profile

            # Get client IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')

            # Use actual account number or generate one
            account_number = profile.account_number or f"CLV{user.id:08d}"

            profile_data = {
                "id": user.id,
                "first_name": user.first_name or "User",
                "last_name": user.last_name or "",
                "email": user.email,
                "balance": 12500.00,  # Mock for now
                "account_number": account_number,
                "ip_address": ip_address,
                "email_verified": profile.email_verified,
                "phone": profile.phone or "",
                "phone_verified": profile.phone_verified,
                "subscription_tier": profile.subscription_tier,
                "avatar_color": profile.avatar_color,
                "cards": []  # Will be populated when cards endpoint is ready
            }

            return Response(profile_data)

        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            logger.error(f"Error in UserProfileView: {str(e)}")
            return Response({"error": "Internal server error"}, status=500)

# -----------------------------------------------------------------
# NEW ENDPOINTS FOR ACCOUNT SETTINGS
# -----------------------------------------------------------------

# Profile Management
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_settings(request):
    """Get extended profile for AccountSettings page"""
    user = request.user
    profile = user.profile
    
    # Calculate security score
    security_score = 0
    if profile.email_verified:
        security_score += 25
    if profile.phone_verified:
        security_score += 25
    if user.settings.two_factor_enabled:
        security_score += 25
    if profile.last_password_change > timezone.now() - timedelta(days=90):
        security_score += 25
    
    profile_data = {
        "name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "username": user.username,
        "email": user.email,
        "email_verified": profile.email_verified,
        "phone": profile.phone or "",
        "phone_verified": profile.phone_verified,
        "account_number": profile.account_number or f"CLV{user.id:08d}",
        "member_since": user.date_joined.strftime("%b %Y"),
        "avatar": get_avatar_initials(user),
        "tier": profile.subscription_tier,
        "security_score": security_score,
        "last_password_change": pretty_time_ago(profile.last_password_change),
        "avatar_color": profile.avatar_color
    }
    
    return Response(profile_data)

# User Settings
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_settings(request):
    """Get user settings from database"""
    user = request.user
    settings = user.settings
    
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
        "subscription_tier": user.profile.subscription_tier,
        "language": settings.language
    }
    
    return Response(settings_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_settings(request):
    """Update user settings in database"""
    data = request.data
    user = request.user
    settings = user.settings
    
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
            setattr(settings, field, data[field])
            updated_fields.append(field)
    
    if updated_fields:
        settings.save()
        create_activity_log(user, 'settings_change', request, {'updated_fields': updated_fields})
        logger.info(f"Updated settings for {user.username}: {updated_fields}")
        return Response({
            "message": "Settings updated successfully",
            "updated_fields": updated_fields
        })
    
    return Response({"error": "No valid fields provided for update"}, status=400)

# Security Alerts
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_alerts(request):
    """Get security alerts from database"""
    user = request.user
    alerts = SecurityAlert.objects.filter(user=user).order_by('-created_at')[:20]
    
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_security_alert(request):
    """Mark alert as resolved"""
    alert_id = request.data.get('alert_id')
    
    if not alert_id:
        return Response({"error": "Alert ID is required"}, status=400)
    
    try:
        alert = SecurityAlert.objects.get(id=alert_id, user=request.user)
        alert.resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        create_activity_log(request.user, 'settings_change', request, {'alert_id': alert_id, 'action': 'resolved'})
        return Response({"message": "Alert resolved successfully"})
    except SecurityAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_score(request):
    """Get calculated security score"""
    user = request.user
    profile = user.profile
    
    security_score = 0
    if profile.email_verified:
        security_score += 25
    if profile.phone_verified:
        security_score += 25
    if user.settings.two_factor_enabled:
        security_score += 25
    if profile.last_password_change > timezone.now() - timedelta(days=90):
        security_score += 25
    
    return Response({"security_score": security_score})

# Connected Devices
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_connected_devices(request):
    """Get connected devices from database"""
    user = request.user
    devices = ConnectedDevice.objects.filter(user=user).order_by('-last_active')
    
    devices_data = []
    for device in devices:
        devices_data.append({
            "id": device.id,
            "name": device.device_name,
            "type": device.device_type,
            "last_active": pretty_time_ago(device.last_active),
            "location": device.location or "Unknown",
            "current": device.is_current,
            "os": device.os or "Unknown",
            "model": device.device_name,
            "connection_type": "wifi",  # Default
            "battery_level": 100  # Default
        })
    
    return Response({"devices": devices_data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_device(request):
    """Disconnect device"""
    device_id = request.data.get('device_id')
    
    if not device_id:
        return Response({"error": "Device ID is required"}, status=400)
    
    try:
        device = ConnectedDevice.objects.get(id=device_id, user=request.user)
        device.delete()
        
        create_activity_log(request.user, 'device_removed', request, {'device_id': device_id})
        return Response({"message": "Device disconnected successfully"})
    except ConnectedDevice.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)

# Activity Logs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_logs(request):
    """Get activity logs from database"""
    user = request.user
    logs = ActivityLog.objects.filter(user=user).order_by('-created_at')[:50]
    
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": log.id,
            "device": "Unknown",  # Would need to parse user_agent
            "browser": log.user_agent[:50] if log.user_agent else "Unknown",
            "ip": log.ip_address or "Unknown",
            "location": log.location or "Unknown",
            "country": "ke",  # Default
            "time": pretty_time_ago(log.created_at),
            "current": False,  # Would need device tracking
            "status": "success",  # Default
            "activity_type": log.activity_type
        })
    
    return Response({"logs": logs_data})

# Data Export
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_user_data(request):
    """Export user data"""
    user = request.user
    profile = user.profile
    settings = user.settings
    
    # Gather data from all models
    data = {
        "profile": {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        },
        "extended_profile": {
            "phone": profile.phone,
            "phone_verified": profile.phone_verified,
            "email_verified": profile.email_verified,
            "subscription_tier": profile.subscription_tier,
            "account_number": profile.account_number,
            "last_password_change": profile.last_password_change.isoformat()
        },
        "settings": {
            "dark_mode": settings.dark_mode,
            "language": settings.language,
            "email_notifications": settings.email_notifications,
            "two_factor_enabled": settings.two_factor_enabled,
            "data_collection": settings.data_collection
        },
        "activity_logs_count": ActivityLog.objects.filter(user=user).count(),
        "security_alerts_count": SecurityAlert.objects.filter(user=user).count(),
        "devices_count": ConnectedDevice.objects.filter(user=user).count(),
        "exported_at": timezone.now().isoformat()
    }
    
    create_activity_log(user, 'settings_change', request, {'action': 'data_export'})
    
    return Response({
        "data": data,
        "filename": f"claverica_export_{user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json",
        "message": "Data exported successfully"
    })

# Password Management
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password"""
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
    user = request.user
    if not user.check_password(old_password):
        return Response({"error": "Current password is incorrect"}, status=400)
    
    # Update password
    user.set_password(new_password)
    user.save()
    
    # Update last_password_change in profile
    profile = user.profile
    profile.last_password_change = timezone.now()
    profile.save()
    
    # Create security alert
    SecurityAlert.objects.create(
        user=user,
        alert_type='password_change',
        severity='medium',
        message='Password was changed successfully',
        metadata={'changed_at': timezone.now().isoformat()}
    )
    
    create_activity_log(user, 'password_change', request)
    
    # Keep user logged in
    update_session_auth_hash(request, user)
    
    return Response({"message": "Password changed successfully"})

# Verification
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email(request):
    """Send email verification"""
    user = request.user
    profile = user.profile
    
    # Generate verification code (in production, store in database)
    code = ''.join(random.choices(string.digits, k=6))
    
    # In production, send actual email
    logger.info(f"Email verification code for {user.email}: {code}")
    
    # For now, just mark as verified for demo
    profile.email_verified = True
    profile.save()
    
    create_activity_log(user, 'email_verification', request)
    
    return Response({
        "message": "Email verification sent. Check your email for the verification code."
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    """Send phone verification"""
    user = request.user
    profile = user.profile
    
    phone_number = request.data.get('phone')
    if phone_number:
        profile.phone = phone_number
        profile.save()
    
    # Generate verification code (in production, store in database)
    code = ''.join(random.choices(string.digits, k=6))
    
    # In production, send actual SMS
    logger.info(f"Phone verification code for {profile.phone}: {code}")
    
    # For now, just return success for demo
    create_activity_log(user, 'phone_verification', request)
    
    return Response({
        "message": "SMS verification sent to your phone number.",
        "requires_code": True  # Frontend should show code input
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_phone_verification(request):
    """Confirm phone verification with code"""
    code = request.data.get('code')
    
    if not code or len(code) != 6 or not code.isdigit():
        return Response({"error": "Invalid verification code"}, status=400)
    
    # In production, verify the code against database
    # For demo, accept any 6-digit code
    user = request.user
    profile = user.profile
    profile.phone_verified = True
    profile.save()
    
    return Response({"message": "Phone verified successfully"})