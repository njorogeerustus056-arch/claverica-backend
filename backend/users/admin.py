from django.contrib import admin
from .models import UserProfile, UserSettings, SecurityAlert, ConnectedDevice, ActivityLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['account', 'phone_number', 'created_at']

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ['account', 'language', 'currency']

@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['account', 'alert_type', 'created_at']

@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ['account', 'device_name', 'last_login']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['account', 'action', 'created_at']
