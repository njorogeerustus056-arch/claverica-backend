from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class TransferRequest(models.Model):
    class Meta:
        app_label = 'transfers'
    
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transfers')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_transfers')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transfer #{self.id}: {self.sender.email} -> {self.receiver.email}"

class TransferLimit(models.Model):
    class Meta:
        app_label = 'transfers'
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfer_limits')
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2, default=50000.00)
    daily_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} transfer limits"
