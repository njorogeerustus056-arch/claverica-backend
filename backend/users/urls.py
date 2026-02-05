# users/urls.py
from django.urls import path
from . import views_profile

urlpatterns = [
    # User settings endpoints
    path('settings/', views_profile.get_account_settings, name='account-settings'),
    path('settings/update/', views_profile.update_settings, name='update-settings'),
    
    # Profile endpoints
    path('profile/update/', views_profile.update_profile, name='update-profile'),
    
    # Security endpoints
    path('password/change/', views_profile.change_password, name='change-password'),
    path('email/verify/', views_profile.verify_email, name='verify-email'),
    path('phone/verify/', views_profile.verify_phone, name='verify-phone'),
    path('2fa/setup/', views_profile.setup_two_factor, name='setup-2fa'),
    
    # Devices & Activity endpoints (NEW)
    path('devices/', views_profile.get_connected_devices, name='get-devices'),
    path('devices/<str:device_id>/remove/', views_profile.remove_device, name='remove-device'),
    path('activity-logs/', views_profile.get_activity_logs, name='activity-logs'),
    
    # Data management endpoints
    path('data/export/', views_profile.export_data, name='export-data'),
    path('delete/', views_profile.delete_account, name='delete-account'),
]