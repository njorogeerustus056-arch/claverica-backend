# users/urls.py
from django.urls import path
from .views import (
    UserProfileView,
    get_profile_settings, get_settings, update_settings,
    get_security_alerts, resolve_security_alert, get_security_score,
    get_connected_devices, disconnect_device,
    get_activity_logs, export_user_data,
    change_password, verify_email, verify_phone, confirm_phone_verification
)

urlpatterns = [
    # Existing endpoint
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # New endpoints for AccountSettings
    path('profile-settings/', get_profile_settings, name='profile-settings'),
    path('settings/', get_settings, name='user-settings'),
    path('settings/update/', update_settings, name='update-settings'),
    
    # Security endpoints
    path('security-alerts/', get_security_alerts, name='security-alerts'),
    path('resolve-alert/', resolve_security_alert, name='resolve-alert'),
    path('security-score/', get_security_score, name='security-score'),
    
    # Device management
    path('devices/', get_connected_devices, name='connected-devices'),
    path('devices/disconnect/', disconnect_device, name='disconnect-device'),
    
    # Activity logs
    path('activity-logs/', get_activity_logs, name='activity-logs'),
    
    # Data export
    path('export-data/', export_user_data, name='export-data'),
    
    # Password management
    path('change-password/', change_password, name='change-password'),
    
    # Verification
    path('verify-email/', verify_email, name='verify-email'),
    path('verify-phone/', verify_phone, name='verify-phone'),
    path('confirm-phone-verification/', confirm_phone_verification, name='confirm-phone-verification'),
]