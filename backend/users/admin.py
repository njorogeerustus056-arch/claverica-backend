from django.contrib import admin
from .models import UserProfile, UserSettings, ActivityLog, ConnectedDevice

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('account', 'date_of_birth', 'bio')
    search_fields = ('account__email', 'account__first_name', 'account__last_name')
    list_filter = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('account', 'date_of_birth', 'bio', 'profile_image')
        }),
        ('Social Links', {
            'fields': ('website', 'twitter', 'linkedin'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('account', 'theme', 'language', 'email_notifications', 'two_factor_enabled')
    list_filter = ('theme', 'profile_visibility', 'email_frequency', 'two_factor_enabled')
    search_fields = ('account__email', 'account__first_name', 'account__last_name')

    fieldsets = (
        ('UI Preferences', {
            'fields': ('theme', 'language', 'timezone')
        }),
        ('Privacy Settings', {
            'fields': ('profile_visibility',)
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications', 'push_notifications', 'email_frequency')
        }),
        ('Security Settings', {
            'fields': ('activity_logs_enabled', 'security_pin_enabled', 'two_factor_enabled', 'biometric_enabled'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ('created_at', 'updated_at')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('account', 'action', 'device', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp', 'country')
    search_fields = ('account__email', 'ip_address', 'device', 'action')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Activity Details', {
            'fields': ('account', 'action', 'description')
        }),
        ('Device Information', {
            'fields': ('device', 'browser', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('Location Information', {
            'fields': ('location', 'country'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )

@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ('account', 'device_name', 'device_type', 'is_current', 'last_active')
    list_filter = ('device_type', 'is_current', 'created_at')
    search_fields = ('account__email', 'device_name', 'device_id')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('account', 'device_id', 'device_name', 'device_type')
        }),
        ('Session Information', {
            'fields': ('is_current', 'last_active')
        }),
        ('Location Information', {
            'fields': ('location', 'country'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'last_active')
