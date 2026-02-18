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
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='transfers')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient_name = models.CharField(max_length=200)
    destination_type = models.CharField(max_length=20, choices=DESTINATION_TYPES)
    destination_details = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    narration = models.TextField(blank=True)
    
    # ADDED: Missing timestamp fields
    tac_sent_at = models.DateTimeField(null=True, blank=True)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    deducted_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    
    # ADDED: Missing reference fields
    external_reference = models.CharField(max_length=100, blank=True)
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer {self.reference}"


class TAC(models.Model):
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
    used_at = models.DateTimeField(null=True, blank=True)  # ADDED: Missing field

    def __str__(self):
        return f"TAC {self.code}"
    
    # ADDED: is_valid() method
    def is_valid(self):
        """Check if TAC is still valid (not expired and pending)"""
        from django.utils import timezone
        return (
            self.status == 'pending' and 
            self.expires_at > timezone.now()
        )


class TransferLog(models.Model):
    LOG_TYPES = [
        ('created', 'Transfer Created'),
        ('tac_sent', 'TAC Sent'),
        ('tac_verified', 'TAC Verified'),
        ('funds_deducted', 'Funds Deducted'),
        ('settlement_completed', 'Settlement Completed'),
        ('status_change', 'Status Change'),
        ('error', 'Error'),
    ]

    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # ADDED: Missing field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id}"


class TransferLimit(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('per_transaction', 'Per Transaction'),  # ADDED: Missing type
    ]

    limit_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ADDED: Missing field

    def __str__(self):
        return f"{self.limit_type} limit"
