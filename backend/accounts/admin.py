# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Account, AccountProfile, AccountSettings, SecurityAlert, ConnectedDevice, ActivityLog

class AccountProfileInline(admin.StackedInline):
    model = AccountProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class AccountSettingsInline(admin.StackedInline):
    model = AccountSettings
    can_delete = False
    verbose_name_plural = 'Settings'

@admin.register(Account)
class AccountAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'document_type', 'document_number', 'street', 'city', 'state', 'zip_code')}),
        ('Employment', {'fields': ('occupation', 'employer', 'income_range')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions',)
    inlines = [AccountProfileInline, AccountSettingsInline]

@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ['account', 'alert_type', 'severity', 'resolved', 'created_at']
    list_filter = ['severity', 'resolved', 'alert_type', 'created_at']
    search_fields = ['account__email', 'message']
    readonly_fields = ['created_at', 'resolved_at']
    ordering = ['-created_at']

@admin.register(ConnectedDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ['account', 'device_name', 'device_type', 'is_current', 'last_active']
    list_filter = ['device_type', 'is_current']
    search_fields = ['account__email', 'device_name', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-last_active']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['account', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['account__email', 'ip_address']
    readonly_fields = ['created_at']
    ordering = ['-created_at']