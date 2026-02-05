from django.db import models
from django.utils import timezone
import uuid

class Transfer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending TAC'),
        ('tac_sent', 'TAC Sent'),
        ('tac_verified', 'TAC Verified'),
        ('funds_deducted', 'Funds Deducted'),
        ('pending_settlement', 'Pending Settlement'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DESTINATION_TYPES = [
        ('bank', 'Bank Account'),
        ('mobile_wallet', 'Mobile Wallet'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    reference = models.CharField(max_length=50, unique=True)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, to_field='account_number')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient_name = models.CharField(max_length=200)
    destination_type = models.CharField(max_length=20, choices=DESTINATION_TYPES)
    destination_details = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    narration = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Transfer {self.reference}"

class TAC(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Use'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"TAC {self.code}"

class TransferLog(models.Model):
    LOG_TYPES = [
        ('created', 'Transfer Created'),
        ('tac_sent', 'TAC Sent'),
        ('tac_verified', 'TAC Verified'),
    ]
    
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE)
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Log {self.id}"

class TransferLimit(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    limit_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.limit_type} limit"
