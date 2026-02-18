from rest_framework import serializers
from .models import Notification, NotificationPreference, NotificationLog

class NotificationSerializer(serializers.ModelSerializer):
    '''Serializer for notifications'''
    # FIXED: Changed from 'account' to 'recipient'
    account_number = serializers.CharField(source='recipient.account_number', read_only=True)
    email = serializers.CharField(source='recipient.email', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    requires_admin_action = serializers.BooleanField(read_only=True)
    action_url = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'account_number', 'email', 'title', 'message',
            'notification_type', 'priority', 'status', 'metadata',
            'created_at', 'read_at', 'expires_at',
            'is_expired', 'is_urgent', 'requires_admin_action', 'action_url'
        ]
        read_only_fields = ['created_at', 'read_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    '''Serializer for admin notifications'''
    # FIXED: Changed from 'account' to 'recipient'
    account_number = serializers.CharField(source='recipient.account_number')
    email = serializers.CharField(source='recipient.email')

    class Meta:
        model = Notification
        fields = [
            'id', 'account_number', 'email', 'title', 'message',
            'notification_type', 'priority', 'metadata',
            'created_at', 'requires_admin_action', 'action_url'
        ]


class NotificationPreferencesSerializer(serializers.ModelSerializer):
    '''Serializer for notification preferences'''
    account_number = serializers.CharField(source='account.account_number', read_only=True)

    class Meta:
        model = NotificationPreference
        fields = [
            'account_number',
            'email_enabled', 'push_enabled', 'in_app_enabled',
            'email_high_priority', 'email_medium_priority', 'email_low_priority',
            'receive_payment_notifications', 'receive_transfer_notifications',
            'receive_tac_notifications', 'receive_account_notifications',
            'receive_admin_notifications',
            'immediate_delivery', 'daily_digest', 'digest_time',
            'updated_at'
        ]


class NotificationLogSerializer(serializers.ModelSerializer):
    '''Serializer for notification logs'''
    notification_title = serializers.CharField(source='notification.title', read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification_title', 'action', 'channel',
            'details', 'metadata', 'created_at'
        ]
