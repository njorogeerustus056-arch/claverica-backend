"""
transfers/models.py - Updated to integrate with compliance system
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from backend.compliance.models import ComplianceRequest, ComplianceProfile

User = get_user_model()


class Transfer(models.Model):
    """Money transfer model integrated with compliance"""
    
    TRANSFER_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('compliance_review', 'Compliance Review'),
        ('awaiting_tac', 'Awaiting TAC'),
        ('awaiting_video_call', 'Awaiting Video Call'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]
    
    # Basic transfer info
    transfer_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfers')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='USD')
    
    # Recipient info
    recipient_name = models.CharField(max_length=255)
    recipient_account = models.CharField(max_length=100)
    recipient_bank = models.CharField(max_length=255, blank=True)
    recipient_country = models.CharField(max_length=2, blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_email = models.EmailField(blank=True)
    
    # Compliance integration
    compliance_request = models.ForeignKey(
        'compliance.ComplianceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer_requests'
    )
    
    # Status fields
    status = models.CharField(max_length=20, choices=TRANSFER_STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # TAC fields (linked to compliance)
    tac_required = models.BooleanField(default=False)
    tac_verified = models.BooleanField(default=False)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Video call fields
    video_call_required = models.BooleanField(default=False)
    video_call_completed = models.BooleanField(default=False)
    video_call_session = models.ForeignKey(
        'compliance.VideoCallSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers'
    )
    
    # Risk assessment
    risk_level = models.CharField(max_length=20, default='low', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional info
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Fees and charges
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        app_label = "transfers"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transfer_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['compliance_request']),
        ]
    
    def __str__(self):
        return f"{self.transfer_id} - {self.user.email} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        if not self.total_amount:
            self.total_amount = self.amount + self.fee + self.tax
        
        # Generate transfer ID if not set
        if not self.transfer_id:
            self.transfer_id = f"TRF-{uuid.uuid4().hex[:12].upper()}"
        
        super().save(*args, **kwargs)
    
    def requires_compliance_check(self):
        """Check if transfer requires compliance review"""
        return self.status in ['draft', 'pending', 'awaiting_tac', 'awaiting_video_call', 'compliance_review']
    
    def can_process(self):
        """Check if transfer can be processed"""
        return (
            self.status in ['pending', 'processing'] and
            not self.tac_required and
            not self.video_call_required and
            self.risk_level != 'high'
        )
    
    def check_kyc_status(self):
        """Check user's KYC status"""
        try:
            profile = ComplianceProfile.objects.get(user=self.user)
            return profile.kyc_status == 'approved'
        except ComplianceProfile.DoesNotExist:
            return False

        """Check user's KYC status"""
        try:
            profile = ComplianceProfile.objects.get(user=self.user)
            return profile.kyc_status == 'approved'
        except ComplianceProfile.DoesNotExist:
            return False

    @property


    def is_high_risk(self):
        """Check if transfer is high risk"""
        return self.risk_level in ['high', 'very_high', 'extreme']

    @property


    def is_pending(self):
        """Check if transfer is in pending state"""
        return self.status in ['pending', 'awaiting_tac', 'awaiting_video_call', 'compliance_review']

    @property


    def is_completed(self):
        """Check if transfer is completed"""
        return self.status == 'completed'

    @property


    def is_high_risk(self):
        """Check if transfer is high risk"""
        return self.risk_level in ['high', 'very_high', 'extreme']

    @property


    def is_pending(self):
        """Check if transfer is in pending state"""
        return self.status in ['pending', 'awaiting_tac', 'awaiting_video_call', 'compliance_review']

    @property


    def is_completed(self):
        """Check if transfer is completed"""
        return self.status == 'completed'

    @property


    def is_high_risk(self):
        """Check if transfer is high risk"""
        return self.risk_level in ['high', 'very_high', 'extreme']

    @property


    def is_pending(self):
        """Check if transfer is in pending state"""
        return self.status in ['pending', 'awaiting_tac', 'awaiting_video_call', 'compliance_review']

    @property


    def is_completed(self):
        """Check if transfer is completed"""
        return self.status == 'completed'

        try:
            profile = ComplianceProfile.objects.get(user=self.user)
            return profile.kyc_status == 'approved'
        except ComplianceProfile.DoesNotExist:
            return False


class TransferLog(models.Model):
    """Audit log for transfer actions"""
    LOG_TYPE_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_change', 'Status Change'),
        ('tac_generated', 'TAC Generated'),
        ('tac_verified', 'TAC Verified'),
        ('video_call_scheduled', 'Video Call Scheduled'),
        ('video_call_completed', 'Video Call Completed'),
        ('compliance_check', 'Compliance Check'),
        ('processed', 'Processed'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=50, choices=LOG_TYPE_CHOICES)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transfer.transfer_id} - {self.log_type}"


class TransferLimit(models.Model):
    """Transfer limits per user/country/currency"""
    LIMIT_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('per_transaction', 'Per Transaction'),
        ('lifetime', 'Lifetime'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='transfer_limits')
    country = models.CharField(max_length=2, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    limit_type = models.CharField(max_length=20, choices=LIMIT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'country', 'currency', 'limit_type']
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Global'
        return f"{user_str} - {self.limit_type} - {self.amount} {self.currency}"