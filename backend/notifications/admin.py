from django.contrib import admin
from .models import Notification, NotificationPreference, NotificationLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'title', 'notification_type', 'status', 'created_at']
    list_filter = ['recipient', 'notification_type', 'status', 'priority']
    search_fields = ['recipient__account_number', 'title', 'message']
    readonly_fields = ['created_at', 'read_at', 'archived_at']
    list_per_page = 50

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['account', 'email_enabled', 'push_enabled', 'in_app_enabled']
    list_filter = ['email_enabled', 'push_enabled', 'in_app_enabled']
    search_fields = ['account__account_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification', 'action', 'channel', 'created_at']
    list_filter = ['action', 'channel']
    search_fields = ['notification__title', 'details']
    readonly_fields = ['created_at']
    list_per_page = 100