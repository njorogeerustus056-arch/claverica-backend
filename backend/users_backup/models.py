from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    class Meta:
        app_label = "users"
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Profile: {self.account.email}"

class UserSettings(models.Model):
    class Meta:
        app_label = "users"
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="settings")
    language = models.CharField(max_length=10, default="en")
    currency = models.CharField(max_length=3, default="USD")
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.account.email} Settings"

class SecurityAlert(models.Model):
    class Meta:
        app_label = "users"
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="security_alerts")
    alert_type = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.account.email} - {self.alert_type}"

class ConnectedDevice(models.Model):
    class Meta:
        app_label = "users"
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connected_devices")
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=100, blank=True)
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.account.email} - {self.device_name}"

class ActivityLog(models.Model):
    class Meta:
        app_label = "users"
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_logs")
    action = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.account.email} - {self.action}"