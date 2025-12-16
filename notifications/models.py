from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Notification(models.Model):
    """User notifications for all activities"""
    NOTIFICATION_TYPES = [
        ('transaction', 'Transaction'),
        ('security', 'Security Alert'),
        ('account', 'Account Update'),
        ('card', 'Card Activity'),
        ('transfer', 'Transfer'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('kyc', 'KYC/Verification'),
        ('savings', 'Savings Goal'),
        ('subscription', 'Subscription'),
        ('promotional', 'Promotional'),
        ('system', 'System'),
        ('reward', 'Reward'),
        ('crypto', 'Crypto Activity'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Rich content
    icon = models.CharField(max_length=50, blank=True, help_text="Lucide icon name or emoji")
    image_url = models.URLField(blank=True, null=True)
    action_url = models.CharField(max_length=500, blank=True, help_text="Frontend route to navigate to")
    
    # Related entities (optional references)
    related_transaction_id = models.CharField(max_length=100, blank=True)
    related_account_id = models.IntegerField(null=True, blank=True)
    related_card_id = models.IntegerField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional data (amounts, names, etc.)")
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery channels
    sent_email = models.BooleanField(default=False)
    sent_push = models.BooleanField(default=False)
    sent_sms = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When notification becomes irrelevant")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def archive(self):
        """Archive notification"""
        self.is_archived = True
        self.save(update_fields=['is_archived'])
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    CHANNEL_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Global settings
    notifications_enabled = models.BooleanField(default=True)
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    
    # Type-specific preferences (JSON for flexibility)
    type_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        {
            "transaction": {"email": true, "push": true, "sms": false},
            "security": {"email": true, "push": true, "sms": true},
            "promotional": {"email": false, "push": false, "sms": false}
        }
        """
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True, default="22:00")
    quiet_hours_end = models.TimeField(null=True, blank=True, default="08:00")
    
    # Frequency limits
    max_notifications_per_hour = models.IntegerField(default=10)
    digest_mode = models.BooleanField(default=False, help_text="Group notifications into daily digest")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def should_send_notification(self, notification_type, channel):
        """Check if notification should be sent based on preferences"""
        if not self.notifications_enabled:
            return False
        
        # Check channel is enabled
        if channel == 'email' and not self.email_enabled:
            return False
        if channel == 'push' and not self.push_enabled:
            return False
        if channel == 'sms' and not self.sms_enabled:
            return False
        
        # Check type-specific preferences
        type_prefs = self.type_preferences.get(notification_type, {})
        if channel in type_prefs:
            return type_prefs[channel]
        
        return True
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        from datetime import time
        now = timezone.localtime(timezone.now()).time()
        
        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # Overnight quiet hours
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class NotificationTemplate(models.Model):
    """Templates for consistent notification creation"""
    template_key = models.CharField(max_length=100, unique=True)
    notification_type = models.CharField(max_length=20)
    priority = models.CharField(max_length=10, default='medium')
    
    title_template = models.CharField(max_length=255, help_text="Use {variable} for placeholders")
    message_template = models.TextField(help_text="Use {variable} for placeholders")
    
    icon = models.CharField(max_length=50, blank=True)
    action_url_template = models.CharField(max_length=500, blank=True)
    
    # Default channel settings
    default_email = models.BooleanField(default=False)
    default_push = models.BooleanField(default=True)
    default_sms = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
    
    def __str__(self):
        return f"{self.template_key} - {self.notification_type}"
    
    def render(self, context):
        """Render template with context variables"""
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        action_url = self.action_url_template.format(**context) if self.action_url_template else ""
        
        return {
            'title': title,
            'message': message,
            'action_url': action_url,
            'icon': self.icon,
            'notification_type': self.notification_type,
            'priority': self.priority,
        }


class PushToken(models.Model):
    """Store push notification tokens for mobile devices"""
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.CharField(max_length=500, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    
    device_name = models.CharField(max_length=255, blank=True)
    device_id = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Push Token'
        verbose_name_plural = 'Push Tokens'
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.token[:20]}..."


class NotificationLog(models.Model):
    """Log of notification delivery attempts"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_logs')
    channel = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    recipient = models.CharField(max_length=255, help_text="Email address, phone number, or token")
    
    error_message = models.TextField(blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.channel} - {self.status}"
