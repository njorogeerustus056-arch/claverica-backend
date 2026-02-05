from django.db import models
from accounts.models import Account  # Use full module path

class UserProfile(models.Model):
    """Extended user profile linked to Account"""
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )

    # Basic profile info
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # Social links
    website = models.URLField(blank=True, null=True)
    twitter = models.CharField(max_length=100, blank=True, null=True)
    linkedin = models.CharField(max_length=100, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.account.email}"

class UserSettings(models.Model):
    """User preferences and settings"""
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='user_settings'
    )

    # UI/UX preferences
    theme = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ])

    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')

    # Privacy settings
    profile_visibility = models.CharField(max_length=20, default='public', choices=[
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends', 'Friends Only')
    ])

    # Notification settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    email_frequency = models.CharField(max_length=20, default='daily', choices=[
        ('realtime', 'Real-time'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest')
    ])

    # Security settings (MISSING FIELDS ADDED)
    activity_logs_enabled = models.BooleanField(default=True)
    security_pin_enabled = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    biometric_enabled = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings: {self.account.email}"

class ActivityLog(models.Model):
    """Track user security and activity events"""
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    
    # Activity details
    action = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Device/browser info
    device = models.CharField(max_length=200, blank=True, null=True)
    browser = models.CharField(max_length=200, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    # Location info
    location = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.account.email}: {self.action} at {self.timestamp}"

class ConnectedDevice(models.Model):
    """Manage user's logged-in devices"""
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='connected_devices'
    )
    
    # Device identification
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=50)
    
    # Session info
    is_current = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    
    # Location data
    location = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_active']
    
    def __str__(self):
        return f"{self.account.email}: {self.device_name} ({self.device_type})"