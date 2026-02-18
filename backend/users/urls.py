# users/urls.py
from django.urls import path
from .views_profile import get_account_settings, update_settings, get_connected_devices, remove_device, get_activity_logs, change_password, verify_email, verify_phone, setup_two_factor, export_data, delete_account
from .views import user_profile, user_me  # Add these imports

urlpatterns = [
    # User settings endpoints
    path('settings/', get_account_settings, name='account-settings'),
    path('settings/update/', update_settings, name='update-settings'),

    # Profile endpoints
    path('profile/', user_profile, name='user-profile'),  # Changed from update_profile
    path('me/', user_me, name='user-me'),

    # Security endpoints
    path('password/change/', change_password, name='change-password'),
    path('email/verify/', verify_email, name='verify-email'),
    path('phone/verify/', verify_phone, name='verify-phone'),
    path('2fa/setup/', setup_two_factor, name='setup-2fa'),

    # Devices & Activity endpoints
    path('devices/', get_connected_devices, name='get-devices'),
    path('devices/<str:device_id>/remove/', remove_device, name='remove-device'),
    path('activity-logs/', get_activity_logs, name='activity-logs'),

    # Data management endpoints
    path('data/export/', export_data, name='export-data'),
    path('delete/', delete_account, name='delete-account'),
]
