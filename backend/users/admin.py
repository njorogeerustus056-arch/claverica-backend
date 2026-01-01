# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserSettings, SecurityAlert, ConnectedDevice, ActivityLog

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    verbose_name_plural = 'Settings'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserSettingsInline)

@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'alert_type', 'severity', 'resolved', 'created_at']
    list_filter = ['severity', 'resolved', 'alert_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'message']
    readonly_fields = ['created_at', 'resolved_at']
    ordering = ['-created_at']

@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'device_type', 'is_current', 'last_active']
    list_filter = ['device_type', 'is_current']
    search_fields = ['user__username', 'device_name', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-last_active']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'ip_address', 'user_agent']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)