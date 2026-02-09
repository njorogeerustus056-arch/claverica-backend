# notifications/models.py - CORRECTED VERSION WITH JSON ENCODER
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
import json

# ============================================
# CUSTOM JSON ENCODER FOR HANDLING MODEL INSTANCES
# ============================================
class ModelSafeJSONEncoder(DjangoJSONEncoder):
    """
    Custom JSON encoder that safely handles Django model instances.
    When a model instance is encountered, it converts it to a serializable dictionary.
    """
    def default(self, obj):
        # Handle Django model instances
        if hasattr(obj, '_meta'):
            return {
                '_model': f"{obj._meta.app_label}.{obj._meta.model_name}",
                'id': obj.pk,
                'str': str(obj),
                # Optional: Include more fields if needed
                # 'repr': repr(obj),
                # 'app': obj._meta.app_label,
                # 'model': obj._meta.model_name,
            }
        
        # Handle UUID objects
        if hasattr(obj, 'hex'):
            return str(obj)
        
        # Handle date/time objects
        if hasattr(obj, 'isoformat'):
            try:
                return obj.isoformat()
            except:
                pass
        
        # Handle Decimal objects
        if hasattr(obj, '__float__'):
            try:
                return float(obj)
            except:
                pass
        
        # For any other non-serializable object, return string representation
        try:
            return super().default(obj)
        except (TypeError, AttributeError):
            return str(obj)

# ============================================
# NOTIFICATION MODEL
# ============================================
class Notification(models.Model):
    TYPE_CHOICES = [
        # Client notifications
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('TRANSFER_INITIATED', 'Transfer Initiated'),
        ('TAC_SENT', 'TAC Sent to Email'),
        ('TAC_VERIFIED', 'TAC Verified'),
        ('TRANSFER_COMPLETED', 'Transfer Completed'),
        ('TRANSFER_FAILED', 'Transfer Failed'),
        ('ACCOUNT_VERIFIED', 'Account Verified'),
        ('ACCOUNT_CREATED', 'Account Created'),
        ('KYC_SUBMITTED', 'KYC Submitted'),
        ('KYC_APPROVED', 'KYC Approved'),
        ('KYC_REJECTED', 'KYC Rejected'),

        # Admin notifications
        ('ADMIN_PAYMENT_PROCESSED', 'Payment Processed (Admin)'),
        ('ADMIN_TAC_REQUIRED', 'TAC Required (Admin)'),
        ('ADMIN_TAC_GENERATED', 'TAC Generated (Admin)'),
        ('ADMIN_SETTLEMENT_REQUIRED', 'Settlement Required (Admin)'),
        ('ADMIN_KYC_REVIEW_REQUIRED', 'KYC Review Required (Admin)'),
        ('ADMIN_NEW_TRANSFER', 'New Transfer Request (Admin)'),
    ]

    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    # ??? CRITICAL FIX: Changed from 'account' to 'recipient' to match database
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # This is 'accounts.Account' in your settings
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default='PAYMENT_RECEIVED'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    status = models.CharField(
        max_length=20,
        choices=[('UNREAD', 'Unread'), ('READ', 'Read'), ('ARCHIVED', 'Archived')],
        default='UNREAD'
    )

    # Metadata for additional context - NOW WITH CUSTOM ENCODER
    metadata = models.JSONField(
        default=dict, 
        blank=True, 
        encoder=ModelSafeJSONEncoder  # ? CRITICAL FIX ADDED HERE
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    # Expiry for time-sensitive notifications
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        user_email = self.recipient.email if self.recipient else 'No User'
        return f'{self.title} - {user_email}'

    def mark_as_read(self):
        """Mark notification as read"""
        if self.status != 'READ':
            self.status = 'READ'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])

    def mark_as_archived(self):
        """Archive the notification"""
        self.status = 'ARCHIVED'
        self.archived_at = timezone.now()
        self.save(update_fields=['status', 'archived_at'])

    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def is_urgent(self):
        """Check if notification is urgent"""
        return self.priority == 'HIGH' or 'ADMIN_' in self.notification_type

    @property
    def requires_admin_action(self):
        """Check if this notification requires admin action"""
        return self.metadata.get('admin_action_required', False)

    @property
    def action_url(self):
        """Get the action URL if available"""
        return self.metadata.get('action_url', None)

    @classmethod
    def get_unread_count(cls, account_number):
        """Get count of unread notifications for an account"""
        return cls.objects.filter(recipient__account_number=account_number, status='UNREAD').count()

    @classmethod
    def get_admin_alerts(cls):
        """Get all admin notifications requiring action"""
        return cls.objects.filter(
            notification_type__in=[
                'ADMIN_TAC_REQUIRED',
                'ADMIN_SETTLEMENT_REQUIRED',
                'ADMIN_KYC_REVIEW_REQUIRED',
                'ADMIN_NEW_TRANSFER'
            ],
            status='UNREAD'
        ).order_by('-created_at')


class NotificationPreference(models.Model):
    """Account preferences for notification delivery"""
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        db_column='user_id'  # Maps to existing database column 'user_id'
    )

    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)

    # Priority-based email preferences
    email_high_priority = models.BooleanField(default=True)
    email_medium_priority = models.BooleanField(default=True)
    email_low_priority = models.BooleanField(default=False)

    # Notification type preferences
    receive_payment_notifications = models.BooleanField(default=True)
    receive_transfer_notifications = models.BooleanField(default=True)
    receive_tac_notifications = models.BooleanField(default=True)
    receive_account_notifications = models.BooleanField(default=True)
    receive_admin_notifications = models.BooleanField(default=True)

    # Delivery timing
    immediate_delivery = models.BooleanField(default=True)
    daily_digest = models.BooleanField(default=False)
    digest_time = models.TimeField(default='18:00')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        account_num = self.account.account_number if self.account else 'No Account'
        return f'Preferences for {account_num}'

    def should_send_email(self, priority):
        """Check if email should be sent based on priority"""
        if not self.email_enabled:
            return False

        priority_map = {
            'HIGH': self.email_high_priority,
            'MEDIUM': self.email_medium_priority,
            'LOW': self.email_low_priority,
        }

        return priority_map.get(priority, True)


class NotificationLog(models.Model):
    """Audit log for notification delivery attempts"""
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('EMAIL_SENT', 'Email Sent'),
        ('EMAIL_FAILED', 'Email Failed'),
        ('PUSH_SENT', 'Push Sent'),
        ('PUSH_FAILED', 'Push Failed'),
        ('READ', 'Marked as Read'),
        ('ARCHIVED', 'Archived'),
        ('EXPIRED', 'Expired'),
    ]

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='delivery_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    channel = models.CharField(
        max_length=20,
        choices=[('EMAIL', 'Email'), ('PUSH', 'Push'), ('IN_APP', 'In-App'), ('SMS', 'SMS')],
        null=True,
        blank=True
    )
    details = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        encoder=ModelSafeJSONEncoder  # ? ALSO FIXED HERE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'

    def __str__(self):
        return f'{self.get_action_display()} - {self.notification.title}'
