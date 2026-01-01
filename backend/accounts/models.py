# accounts/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# -----------------------------
# Custom User Manager
# -----------------------------
class AccountManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Create profile and settings automatically
        AccountProfile.objects.create(account=user)
        AccountSettings.objects.create(account=user)
        
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, first_name, last_name, password, **extra_fields)

# -----------------------------
# Account Model
# -----------------------------
class Account(AbstractBaseUser, PermissionsMixin):
    # Personal Info
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Document Info
    DOC_TYPE_CHOICES = [
        ('drivers-license', "Driver's License"),
        ('ssn', "SSN"),
        ('tfn', "TFN"),
        ('national-id', "National ID"),
        ('passport', "Passport"),
    ]
    document_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, blank=True, null=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    # Address
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    # Employment (optional)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    employer = models.CharField(max_length=100, blank=True, null=True)
    INCOME_RANGE_CHOICES = [
        ('<25k', 'Below $25,000'),
        ('25k-50k', '$25,000 – $50,000'),
        ('50k-100k', '$50,000 – $100,000'),
        ('100k-200k', '$100,000 – $200,000'),
        ('>200k', 'Above $200,000'),
    ]
    income_range = models.CharField(max_length=20, choices=INCOME_RANGE_CHOICES, blank=True, null=True)

    # Permissions / Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Override PermissionsMixin fields to avoid clashes
    groups = models.ManyToManyField(
        Group,
        related_name='account_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='account_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = AccountManager()

    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name

# -----------------------------
# Account Profile Model
# -----------------------------
class AccountProfile(models.Model):
    """Extended account profile information"""
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='profile')
    phone_verified = models.BooleanField(default=False)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    avatar_color = models.CharField(max_length=7, default='#3B82F6')
    subscription_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic')
    last_password_change = models.DateTimeField(default=timezone.now)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account.email} Profile"

# -----------------------------
# Account Settings Model
# -----------------------------
class AccountSettings(models.Model):
    """Account preferences and settings"""
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='settings')
    
    # Security Settings
    activity_logs_enabled = models.BooleanField(default=True)
    security_pin_enabled = models.BooleanField(default=True)
    two_factor_enabled = models.BooleanField(default=True)
    biometric_enabled = models.BooleanField(default=False)
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Privacy Settings
    data_collection = models.CharField(
        max_length=20,
        choices=[('all', 'All'), ('essential', 'Essential Only')],
        default='all'
    )
    
    # Appearance
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(max_length=10, default='en')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account.email} Settings"

# -----------------------------
# Security Alert Model
# -----------------------------
class SecurityAlert(models.Model):
    """Security alerts and notifications"""
    ALERT_TYPES = [
        ('new_device', 'New Device Login'),
        ('location_change', 'Location Change'),
        ('password_change', 'Password Changed'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('login_attempt', 'Failed Login Attempt'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.account.email} - {self.alert_type} ({self.severity})"
    
    class Meta:
        ordering = ['-created_at']

# -----------------------------
# Connected Device Model
# -----------------------------
class ConnectedDevice(models.Model):
    """Track account's connected devices"""
    DEVICE_TYPES = [
        ('mobile', 'Mobile'),
        ('desktop', 'Desktop'),
        ('tablet', 'Tablet'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    os = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    last_active = models.DateTimeField(default=timezone.now)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account.email} - {self.device_name}"
    
    class Meta:
        ordering = ['-last_active']
        unique_together = ['account', 'device_id']

# -----------------------------
# Activity Log Model
# -----------------------------
class ActivityLog(models.Model):
    """Account activity logs"""
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('transaction', 'Transaction'),
        ('settings_change', 'Settings Change'),
        ('password_change', 'Password Change'),
        ('device_added', 'Device Added'),
        ('device_removed', 'Device Removed'),
        ('email_verification', 'Email Verification'),
        ('phone_verification', 'Phone Verification'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account.email} - {self.activity_type}"
    
    class Meta:
        ordering = ['-created_at']