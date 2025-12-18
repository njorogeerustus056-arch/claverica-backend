from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    NotificationLog, NotificationDevice
)


def badge(value: str, color_map: dict, default_color: str = '#6b7280') -> str:
    """Helper to render colored badges."""
    color = color_map.get(value, default_color)
    return format_html(
        '<span style="background-color: {}; color: white; padding: 3px 10px; '
        'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
        color,
        value.capitalize()
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'notification_id_short', 'user', 'title', 'notification_type',
        'priority_badge', 'is_read', 'is_archived', 'created_at'
    )
    list_filter = ('notification_type', 'priority', 'is_read', 'is_archived', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email', 'notification_id')
    readonly_fields = ('notification_id', 'created_at', 'read_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Details', {'fields': ('notification_id', 'user', 'notification_type', 'priority')}),
        ('Content', {'fields': ('title', 'message', 'action_url', 'action_label')}),
        ('Status', {'fields': ('is_read', 'is_archived', 'read_at')}),
        ('Related Information', {'fields': ('related_transaction_id', 'related_account_id', 'metadata'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'expires_at'), 'classes': ('collapse',)}),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'archive_notifications']
    
    def notification_id_short(self, obj):
        return str(obj.notification_id)[:8]
    notification_id_short.short_description = 'ID'
    
    def priority_badge(self, obj):
        colors = {'low': '#10b981', 'medium': '#f59e0b', 'high': '#ef4444', 'urgent': '#dc2626'}
        return badge(obj.get_priority_display().lower(), colors)
    priority_badge.short_description = 'Priority'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'
    
    def archive_notifications(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f'{updated} notifications archived.')
    archive_notifications.short_description = 'Archive selected notifications'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled', 'updated_at')
    list_filter = ('in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled',
                   'transaction_notifications', 'security_notifications')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Channels', {'fields': ('in_app_enabled', 'email_enabled', 'sms_enabled', 'push_enabled')}),
        ('Notification Types', {'fields': (
            'transaction_notifications', 'security_notifications',
            'account_notifications', 'card_notifications',
            'payment_notifications', 'promotional_notifications'
        )}),
        ('Quiet Hours', {'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'), 'classes': ('collapse',)}),
        ('Digest Settings', {'fields': ('digest_enabled', 'digest_time'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('template_type', 'notification_type', 'priority_badge', 'is_active', 'updated_at')
    list_filter = ('notification_type', 'priority', 'is_active', 'created_at')
    search_fields = ('template_type', 'title_template', 'message_template')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Template Information', {'fields': ('template_type', 'notification_type', 'priority', 'is_active')}),
        ('Content Templates', {'fields': ('title_template', 'message_template'), 'description': 'Use {variable_name} for dynamic content'}),
        ('Action', {'fields': ('action_url_template', 'action_label')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def priority_badge(self, obj):
        colors = {'low': '#10b981', 'medium': '#f59e0b', 'high': '#ef4444', 'urgent': '#dc2626'}
        return badge(obj.get_priority_display().lower(), colors)
    priority_badge.short_description = 'Priority'


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'channel', 'status_badge', 'sent_at', 'delivered_at', 'read_at')
    list_filter = ('channel', 'status', 'sent_at')
    search_fields = ('notification__title', 'notification__user__username', 'error_message')
    readonly_fields = ('sent_at', 'delivered_at', 'read_at')
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Log Details', {'fields': ('notification', 'channel', 'status')}),
        ('Timestamps', {'fields': ('sent_at', 'delivered_at', 'read_at')}),
        ('Error Information', {'fields': ('error_message',), 'classes': ('collapse',)}),
        ('Metadata', {'fields': ('metadata',), 'classes': ('collapse',)}),
    )
    
    def status_badge(self, obj):
        colors = {'sent': '#6b7280', 'delivered': '#3b82f6', 'read': '#10b981', 'failed': '#ef4444'}
        return badge(obj.get_status_display().lower(), colors)
    status_badge.short_description = 'Status'


@admin.register(NotificationDevice)
class NotificationDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'device_name', 'is_active_badge', 'registered_at', 'last_used_at')
    list_filter = ('device_type', 'is_active', 'registered_at')
    search_fields = ('user__username', 'user__email', 'device_name', 'device_token')
    readonly_fields = ('registered_at', 'last_used_at')
    
    fieldsets = (
        ('Device Information', {'fields': ('user', 'device_type', 'device_name', 'device_token')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('registered_at', 'last_used_at'), 'classes': ('collapse',)}),
    )
    
    actions = ['activate_devices', 'deactivate_devices']
    
    def is_active_badge(self, obj):
        color, text = ('#10b981', 'Active') if obj.is_active else ('#ef4444', 'Inactive')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            text
        )
    is_active_badge.short_description = 'Status'
    
    def activate_devices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} devices activated.')
    activate_devices.short_description = 'Activate selected devices'
    
    def deactivate_devices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} devices deactivated.')
    deactivate_devices.short_description = 'Deactivate selected devices'
