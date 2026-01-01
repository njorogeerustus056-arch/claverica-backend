# notifications/models.py
from django.db import models
from django.conf import settings  # Use custom Account model
from django.utils import timezone
import uuid


class Notification(models.Model):
    """User notifications for account activities"""

    NOTIFICATION_TYPES = [
        ('transaction', 'Transaction'),
        ('security', 'Security Alert'),
        ('account', 'Account Update'),
        ('card', 'Card Activity'),
        ('payment', 'Payment'),
        ('transfer', 'Transfer'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('kyc', 'KYC Verification'),
        ('promotion', 'Promotion'),
        ('system', 'System Notification'),
        ('loan', 'Loan Update'),
        ('savings', 'Savings Goal'),
        ('subscription', 'Subscription'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    notification_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')

    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    action_url = models.CharField(max_length=500, blank=True, help_text="URL to redirect on click")
    action_label = models.CharField(max_length=100, blank=True, help_text="Button text like 'View Transaction'")

    related_transaction_id = models.UUIDField(null=True, blank=True)
    related_account_id = models.IntegerField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True, help_text="Extra data for notification")

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Auto-archive after this date")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_unread(self):
        self.is_read = False
        self.read_at = None
        self.save()

    def archive(self):
        self.is_archived = True
        self.save()

    @property
    def time_ago(self):
        from django.utils.timesince import timesince
        return timesince(self.created_at)


class NotificationPreference(models.Model):
    """User preferences for notifications"""

    CHANNEL_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')

    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)

    transaction_notifications = models.BooleanField(default=True)
    security_notifications = models.BooleanField(default=True)
    account_notifications = models.BooleanField(default=True)
    card_notifications = models.BooleanField(default=True)
    payment_notifications = models.BooleanField(default=True)
    promotional_notifications = models.BooleanField(default=False)

    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)

    digest_enabled = models.BooleanField(default=False, help_text="Receive daily digest instead of instant")
    digest_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Notification Preferences"

    class Meta:
        verbose_name_plural = 'Notification Preferences'


class NotificationTemplate(models.Model):
    """Templates for generating notifications"""

    TEMPLATE_TYPES = [
        ('transaction_success', 'Transaction Successful'),
        ('transaction_failed', 'Transaction Failed'),
        ('login_new_device', 'New Device Login'),
        ('password_changed', 'Password Changed'),
        ('card_issued', 'Card Issued'),
        ('card_blocked', 'Card Blocked'),
        ('payment_received', 'Payment Received'),
        ('transfer_completed', 'Transfer Completed'),
        ('kyc_approved', 'KYC Approved'),
        ('kyc_rejected', 'KYC Rejected'),
        ('low_balance', 'Low Balance Alert'),
        ('savings_goal_reached', 'Savings Goal Reached'),
        ('subscription_reminder', 'Subscription Reminder'),
    ]

    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    title_template = models.CharField(max_length=255, help_text="Use {variable} for dynamic content")
    message_template = models.TextField(help_text="Use {variable} for dynamic content")
    notification_type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=Notification.PRIORITY_LEVELS, default='medium')

    action_url_template = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Template: {self.get_template_type_display()}"

    def render(self, context=None):
        """Render template safely with context data"""
        context = context or {}
        try:
            title = self.title_template.format(**context)
        except KeyError:
            title = self.title_template
        try:
            message = self.message_template.format(**context)
        except KeyError:
            message = self.message_template
        action_url = ""
        if self.action_url_template:
            try:
                action_url = self.action_url_template.format(**context)
            except KeyError:
                action_url = self.action_url_template
        return {
            'title': title,
            'message': message,
            'action_url': action_url,
            'action_label': self.action_label,
            'notification_type': self.notification_type,
            'priority': self.priority,
        }


class NotificationLog(models.Model):
    """Log of sent notifications for tracking"""

    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    channel = models.CharField(max_length=20, choices=NotificationPreference.CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.notification.title} - {self.channel} - {self.status}"

    class Meta:
        ordering = ['-sent_at']


class NotificationDevice(models.Model):
    """User devices for push notifications"""

    DEVICE_TYPES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_devices')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    device_token = models.CharField(max_length=500, unique=True)
    device_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    registered_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_type} - {self.device_name or 'Unnamed'}"

    class Meta:
        ordering = ['-last_used_at']
