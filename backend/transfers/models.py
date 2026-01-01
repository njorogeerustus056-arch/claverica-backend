from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class Recipient(models.Model):
    """Model for storing transfer recipients (banks, fintech, crypto)"""
    
    RECIPIENT_TYPES = (
        ('bank', 'Bank'),
        ('fintech', 'Fintech'),
        ('crypto', 'Cryptocurrency'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipients')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES)
    
    # Basic Info
    name = models.CharField(max_length=255, help_text="Recipient name or institution")
    country = models.CharField(max_length=100)
    logo = models.CharField(max_length=10, default="🏦", help_text="Emoji or icon")
    
    # Bank/Fintech Details
    account_number = models.CharField(max_length=100, blank=True, null=True)
    account_holder = models.CharField(max_length=255, blank=True, null=True)
    swift_code = models.CharField(max_length=50, blank=True, null=True)
    iban = models.CharField(max_length=50, blank=True, null=True)
    routing_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Crypto Details
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    network = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., TRC20, ERC20, BTC")
    
    # Metadata
    is_favorite = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_favorite', '-created_at']
        indexes = [
            models.Index(fields=['user', 'recipient_type']),
            models.Index(fields=['is_favorite']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.country}) - {self.get_recipient_type_display()}"


class Transfer(models.Model):
    """Model for transfer transactions"""
    
    TRANSFER_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('compliance_review', 'Compliance Review'),
    )
    
    TRANSFER_TYPES = (
        ('bank', 'Bank Transfer'),
        ('fintech', 'Fintech Transfer'),
        ('crypto', 'Crypto Transfer'),
        ('international', 'International Transfer'),
        ('internal', 'Internal Transfer'),
    )
    
    # Transfer ID
    transfer_id = models.CharField(max_length=100, unique=True, editable=False)
    
    # Parties
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_transfers')
    recipient = models.ForeignKey(Recipient, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')
    
    # Transfer Details
    transfer_type = models.CharField(max_length=30, choices=TRANSFER_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=10, default='USD')
    
    # Fee & Total
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    # Status & Tracking
    status = models.CharField(max_length=30, choices=TRANSFER_STATUS, default='pending')
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Compliance
    requires_tac = models.BooleanField(default=False, help_text="Requires Transfer Authorization Code")
    tac_verified = models.BooleanField(default=False)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    
    compliance_status = models.CharField(max_length=50, default='pending', help_text="KYC/AML status")
    compliance_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional recipient info (if not using Recipient model)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_account = models.CharField(max_length=255, blank=True, null=True)
    recipient_bank = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['transfer_id']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate transfer ID if not exists
        if not self.transfer_id:
            import uuid
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4())[:8].upper()
            self.transfer_id = f"TRF-{date_str}-{unique_id}"
        
        # Calculate total amount
        self.total_amount = self.amount + self.fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transfer_id} - {self.sender.email} → {self.recipient_name or 'Unknown'} - {self.amount} {self.currency}"


class TransferLog(models.Model):
    """Model for tracking transfer status changes"""
    
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=30)
    message = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transfer.transfer_id} - {self.status} at {self.created_at}"


class TACCode(models.Model):
    """Model for Transfer Authorization Codes"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tac_codes')
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='tac_codes', null=True, blank=True)
    
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"TAC-{self.code} for {self.user.email}"
    
    def is_valid(self):
        """Check if TAC code is still valid"""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()