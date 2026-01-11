# users/urls.py - UPDATED
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/create/', views.create_or_update_profile, name='create-profile'),
    path('profile/update/', views.update_profile_partial, name='update-profile-partial'),
    path('profile-settings/', views.get_profile_settings, name='profile-settings'),
    
    # Settings endpoints
    path('settings/', views.get_settings, name='user-settings'),
    path('settings/update/', views.update_settings, name='update-settings'),
    
    # Security endpoints
    path('security-alerts/', views.get_security_alerts, name='security-alerts'),
    path('resolve-alert/', views.resolve_security_alert, name='resolve-alert'),
    path('security-score/', views.get_security_score, name='security-score'),
    
    # Device management
    path('devices/', views.get_connected_devices, name='connected-devices'),
    path('devices/disconnect/', views.disconnect_device, name='disconnect-device'),
    
    # Activity logs
    path('activity-logs/', views.get_activity_logs, name='activity-logs'),
    
    # Data export
    path('export-data/', views.export_user_data, name='export-data'),
    
    # Password management
    path('change-password/', views.change_password, name='change-password'),
    
    # Verification
    path('verify-email/', views.verify_email, name='verify-email'),
    path('verify-phone/', views.verify_phone, name='verify-phone'),
    path('confirm-phone-verification/', views.confirm_phone_verification, name='confirm-phone-verification'),
]