from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid

class Transfer(models.Model):
    """Transfer model for outbound money movements"""
    
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
    
    # Core fields
    reference = models.CharField(max_length=50, unique=True, default=lambda: f"TRF-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}")
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='transfers', to_field='account_number')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient_name = models.CharField(max_length=200)
    
    # Destination details
    destination_type = models.CharField(max_length=20, choices=DESTINATION_TYPES)
    destination_details = models.JSONField(default=dict)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    narration = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    tac_sent_at = models.DateTimeField(null=True, blank=True)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    deducted_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    
    # External reference
    external_reference = models.CharField(max_length=100, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.reference} - \ to {self.recipient_name}"

class TAC(models.Model):
    """Transfer Authorization Code (manually sent by admin)"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Use'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    ]
    
    transfer = models.OneToOneField(Transfer, on_delete=models.CASCADE, related_name='tac')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    used_at = models.DateTimeField(null=True, blank=True)
    
    def is_valid(self):
        return (self.status == 'pending' and 
                self.expires_at > timezone.now())

class TransferLog(models.Model):
    """Audit trail for transfer operations"""
    
    LOG_TYPES = [
        ('created', 'Transfer Created'),
        ('tac_sent', 'TAC Sent'),
        ('tac_verified', 'TAC Verified'),
        ('funds_deducted', 'Funds Deducted'),
        ('settlement_started', 'Settlement Started'),
        ('settlement_completed', 'Settlement Completed'),
        ('status_change', 'Status Changed'),
        ('error', 'Error'),
    ]
    
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    message = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.created_at}"

class TransferLimit(models.Model):
    """Business rules for transfer limits"""
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('per_transaction', 'Per Transaction'),
    ]
    
    limit_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['limit_type']
    
    def __str__(self):
        return f"{self.get_limit_type_display()} Limit: \"

