from rest_framework import serializers
from django.conf import settings
from .models import (
    Notification, NotificationPreference, NotificationTemplate,
    NotificationLog, NotificationDevice
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    time_ago = serializers.ReadOnlyField()

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_id', 'user', 'notification_type', 'title',
            'message', 'priority', 'is_read', 'is_archived', 'read_at',
            'action_url', 'action_label', 'related_transaction_id',
            'related_account_id', 'metadata', 'created_at', 'expires_at',
            'time_ago'
        ]
        read_only_fields = ['id', 'notification_id', 'created_at', 'read_at', 'time_ago']


class NotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'notification_type', 'title', 'message', 'priority',
            'action_url', 'action_label', 'related_transaction_id',
            'related_account_id', 'metadata', 'expires_at'
        ]

    def create(self, validated_data):
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User context is required.")
        validated_data['user'] = user
        return Notification.objects.create(**validated_data)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'in_app_enabled', 'email_enabled', 'sms_enabled',
            'push_enabled', 'transaction_notifications', 'security_notifications',
            'account_notifications', 'card_notifications', 'payment_notifications',
            'promotional_notifications', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'digest_enabled', 'digest_time', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'template_type', 'title_template', 'message_template',
            'notification_type', 'priority', 'action_url_template',
            'action_label', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)

    class Meta:
        model = NotificationLog
        fields = [
            'id', 'notification', 'channel', 'status', 'sent_at',
            'delivered_at', 'read_at', 'error_message', 'metadata'
        ]
        read_only_fields = ['id', 'sent_at', 'delivered_at', 'read_at']


class NotificationDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDevice
        fields = [
            'id', 'user', 'device_type', 'device_token', 'device_name',
            'is_active', 'registered_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'user', 'registered_at', 'last_used_at']

    def create(self, validated_data):
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User context is required.")
        validated_data['user'] = user

        # Deactivate old devices with same token
        NotificationDevice.objects.filter(device_token=validated_data['device_token']).update(is_active=False)

        return NotificationDevice.objects.create(**validated_data)


class NotificationStatsSerializer(serializers.Serializer):
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_count = serializers.IntegerField()
    archived_count = serializers.IntegerField()
    by_type = serializers.DictField()
    by_priority = serializers.DictField()
    recent_unread = NotificationSerializer(many=True, read_only=True)


class BulkNotificationSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())
    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    priority = serializers.ChoiceField(choices=Notification.PRIORITY_LEVELS, default='medium')
    action_url = serializers.CharField(required=False, allow_blank=True)
    action_label = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, default=dict)

    def create_notifications(self):
        user_ids = self.validated_data.get('user_ids', [])
        users = settings.AUTH_USER_MODEL.objects.filter(id__in=user_ids)
        notifications = [
            Notification(
                user=user,
                notification_type=self.validated_data['notification_type'],
                title=self.validated_data['title'],
                message=self.validated_data['message'],
                priority=self.validated_data['priority'],
                action_url=self.validated_data.get('action_url', ''),
                action_label=self.validated_data.get('action_label', ''),
                metadata=self.validated_data.get('metadata', {}),
            ) for user in users
        ]
        return Notification.objects.bulk_create(notifications)


class MarkAsReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(child=serializers.IntegerField())
