# users/views_profile.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import check_password
import json
import csv
from io import StringIO

from accounts.models import Account
from .models import UserProfile, UserSettings, ActivityLog, ConnectedDevice

# ============================
# USER PROFILE ENDPOINTS
# ============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_account_settings(request):
    """Get user settings"""
    try:
        settings = request.user.user_settings
        return Response({
            'theme': settings.theme,
            'language': settings.language,
            'timezone': settings.timezone,
            'profile_visibility': settings.profile_visibility,
            'email_notifications': settings.email_notifications,
            'sms_notifications': settings.sms_notifications,
            'email_frequency': settings.email_frequency,
            'two_factor_enabled': settings.two_factor_enabled,
            'push_notifications': settings.push_notifications
        })
    except UserSettings.DoesNotExist:
        return Response({
            'theme': 'light',
            'language': 'en',
            'timezone': 'UTC',
            'profile_visibility': 'public',
            'email_notifications': True,
            'sms_notifications': True,
            'email_frequency': 'daily',
            'two_factor_enabled': False,
            'push_notifications': True
        })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_settings(request):
    """Update user settings"""
    try:
        settings = request.user.user_settings

        # Allowed fields to update
        allowed_fields = [
            'theme', 'language', 'timezone', 'profile_visibility',
            'email_notifications', 'sms_notifications', 'email_frequency',
            'two_factor_enabled', 'push_notifications', 'activity_logs_enabled',
            'security_pin_enabled', 'biometric_enabled'
        ]

        # Update only allowed fields
        for field in allowed_fields:
            if field in request.data:
                setattr(settings, field, request.data[field])

        settings.save()

        return Response({
            'success': True,
            'message': 'Settings updated successfully'
        })
    except UserSettings.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Settings not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    try:
        profile = request.user.user_profile

        # Allowed profile fields
        allowed_fields = ['date_of_birth', 'bio', 'website', 'twitter', 'linkedin']

        # Update only allowed fields
        for field in allowed_fields:
            if field in request.data:
                setattr(profile, field, request.data[field])

        # Handle profile image separately
        if 'profile_image' in request.data:
            profile.profile_image = request.data['profile_image']

        profile.save()

        return Response({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Profile not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        return Response({
            'success': False,
            'message': 'All password fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({
            'success': False,
            'message': 'New passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    # Verify current password
    if not check_password(current_password, user.password):
        return Response({
            'success': False,
            'message': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Set new password
    user.set_password(new_password)
    user.save()

    # Log the activity
    ActivityLog.objects.create(
        account=user,
        action='password_changed',
        description='User changed their password',
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return Response({
        'success': True,
        'message': 'Password changed successfully'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_email(request):
    """Send email verification"""
    # TODO: Implement email verification logic
    return Response({
        'success': True,
        'message': 'Email verification sent'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    """Send phone verification"""
    # TODO: Implement phone verification logic
    return Response({
        'success': True,
        'message': 'Phone verification sent'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_two_factor(request):
    """Setup two-factor authentication"""
    # TODO: Implement 2FA setup logic
    return Response({
        'success': True,
        'message': '2FA setup initiated'
    })

# ============================
# NEW ENDPOINTS ADDED BELOW
# ============================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_connected_devices(request):
    """Get all connected devices for user"""
    try:
        devices = ConnectedDevice.objects.filter(account=request.user)
        data = [{
            'id': device.id,
            'device_id': device.device_id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'last_active': device.last_active,
            'location': device.location,
            'country': device.country,
            'is_current': device.is_current,
            'created_at': device.created_at
        } for device in devices]
        
        return Response({
            'success': True,
            'devices': data,
            'count': len(data)
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching devices: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_activity_logs(request):
    """Get user activity logs"""
    try:
        logs = ActivityLog.objects.filter(account=request.user).order_by('-timestamp')[:50]  # Last 50 logs
        data = [{
            'id': log.id,
            'action': log.action,
            'description': log.description,
            'timestamp': log.timestamp,
            'device': log.device,
            'browser': log.browser,
            'ip_address': log.ip_address,
            'location': log.location,
            'country': log.country
        } for log in logs]
        
        return Response({
            'success': True,
            'logs': data,
            'count': len(data)
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching activity logs: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_device(request, device_id):
    """Remove a connected device"""
    try:
        device = ConnectedDevice.objects.get(device_id=device_id, account=request.user)
        device.delete()

        # Log the activity
        ActivityLog.objects.create(
            account=request.user,
            action='device_removed',
            description=f'Removed device: {device.device_name}',
            device=device.device_type,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            'success': True,
            'message': 'Device removed successfully'
        })
    except ConnectedDevice.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """Export user data"""
    user = request.user

    # Create CSV data
    output = StringIO()
    writer = csv.writer(output)

    # Write user data
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Email', user.email])
    writer.writerow(['Account Number', user.account_number])
    writer.writerow(['First Name', user.first_name])
    writer.writerow(['Last Name', user.last_name])
    writer.writerow(['Phone', user.phone])
    writer.writerow(['Date Joined', user.date_joined])
    writer.writerow(['Last Login', user.last_login])

    # Add profile data if exists
    try:
        profile = user.user_profile
        writer.writerow(['Bio', profile.bio])
        writer.writerow(['Date of Birth', profile.date_of_birth])
        writer.writerow(['Website', profile.website])
        writer.writerow(['Twitter', profile.twitter])
        writer.writerow(['LinkedIn', profile.linkedin])
    except UserProfile.DoesNotExist:
        pass

    # Get CSV data
    csv_data = output.getvalue()

    return Response({
        'success': True,
        'data': csv_data,
        'filename': f'user_data_{user.account_number}.csv'
    })

@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """Delete user account (requires confirmation)"""
    confirmation = request.data.get('confirmation')

    if confirmation != 'DELETE MY ACCOUNT':
        return Response({
            'success': False,
            'message': 'Confirmation phrase is required: "DELETE MY ACCOUNT"'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    # Log the activity before deletion
    ActivityLog.objects.create(
        account=user,
        action='account_deletion_requested',
        description='User requested account deletion',
        ip_address=request.META.get('REMOTE_ADDR')
    )

    # For security, we'll deactivate instead of delete
    user.is_active = False
    user.save()

    return Response({
        'success': True,
        'message': 'Account deactivated successfully. Contact support to restore.'
    })