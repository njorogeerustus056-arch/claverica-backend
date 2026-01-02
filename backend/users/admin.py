# users/admin.py - UPDATED
from django.contrib import admin
from .models import UserProfile, UserSettings, SecurityAlert, ConnectedDevice, ActivityLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('account_email', 'phone', 'subscription_tier', 'phone_verified', 'created_at')
    search_fields = ('account__email', 'account__first_name', 'phone')
    list_filter = ('subscription_tier', 'phone_verified', 'created_at')
    
    def account_email(self, obj):
        return obj.account.email
    account_email.short_description = 'Account Email'


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('account_email', 'two_factor_enabled', 'email_notifications', 'dark_mode')
    search_fields = ('account__email', 'account__first_name')
    list_filter = ('two_factor_enabled', 'email_notifications', 'dark_mode')
    
    def account_email(self, obj):
        return obj.account.email
    account_email.short_description = 'Account Email'


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['account_email', 'alert_type', 'severity', 'resolved', 'created_at']
    list_filter = ['severity', 'resolved', 'alert_type', 'created_at']
    search_fields = ['account__email', 'account__first_name', 'message']
    readonly_fields = ['created_at', 'resolved_at']
    ordering = ['-created_at']
    
    def account_email(self, obj):
        return obj.account.email
    account_email.short_description = 'Account Email'


@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ['account_email', 'device_name', 'device_type', 'is_current', 'last_active']
    list_filter = ['device_type', 'is_current']
    search_fields = ['account__email', 'device_name', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-last_active']
    
    def account_email(self, obj):
        return obj.account.email
    account_email.short_description = 'Account Email'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['account_email', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['account__email', 'ip_address', 'user_agent']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def account_email(self, obj):
        return obj.account.email
    account_email.short_description = 'Account Email'