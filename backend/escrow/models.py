# escrow/models.py - UPDATED FOR COMPLIANCE INTEGRATION

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from decimal import Decimal

class Escrow(models.Model):
    """
    Escrow model for secure transactions between parties
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('funded', 'Funded'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DISPUTE_STATUS_CHOICES = [
        ('none', 'No Dispute'),
        ('opened', 'Dispute Opened'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
    ]
    
    # Removed custom UUID PK - use default BigAutoField (integer)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # COMMENTED OUT

    escrow_id = models.CharField(max_length=100, unique=True, editable=False)

    # Parties involved
    sender_id = models.CharField(max_length=255, db_index=True)
    sender_name = models.CharField(max_length=255)
    receiver_id = models.CharField(max_length=255, db_index=True)
    receiver_name = models.CharField(max_length=255)

    # Transaction details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    fee = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Escrow information
    title = models.CharField(max_length=255)
    description = models.TextField()
    terms_and_conditions = models.TextField(blank=True, null=True)

    # Status and flags
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_released = models.BooleanField(default=False)
    release_approved_by_sender = models.BooleanField(default=False)
    release_approved_by_receiver = models.BooleanField(default=False)

    # Dispute management
    dispute_status = models.CharField(max_length=20, choices=DISPUTE_STATUS_CHOICES, default='none')
    dispute_reason = models.TextField(blank=True, null=True)
    dispute_opened_by = models.CharField(max_length=255, blank=True, null=True)
    dispute_opened_at = models.DateTimeField(null=True, blank=True)
    
    # NEW: Compliance integration
    compliance_reference = models.CharField(max_length=100, blank=True, help_text="Reference to compliance app for dispute handling")
    requires_compliance_approval = models.BooleanField(default=False)

    # Important dates
    expected_release_date = models.DateTimeField(null=True, blank=True)
    funded_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender_id', '-created_at']),
            models.Index(fields=['receiver_id', '-created_at']),
            models.Index(fields=['escrow_id']),
            models.Index(fields=['status']),
            models.Index(fields=['compliance_reference']),  # NEW: Index for compliance lookup
        ]

    def __str__(self):
        return f"{self.escrow_id}: {self.sender_name} → {self.receiver_name} | ${self.amount}"

    def save(self, *args, **kwargs):
        if not self.escrow_id:
            import random
            import string
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.escrow_id = f"ESC/{random_str}-{random.randint(1000, 9999)}"
        self.total_amount = self.amount + self.fee
        super().save(*args, **kwargs)

    def can_release(self):
        """Check if escrow can be released"""
        return self.status == 'funded' and not self.is_released

    def release(self):
        """Release escrow funds"""
        if not self.can_release():
            return False
        self.status = 'released'
        self.is_released = True
        self.released_at = timezone.now()
        self.save(update_fields=[
            'status',
            'is_released',
            'released_at',
            'updated_at'
        ])
        return True
    
    def requires_compliance_check(self):
        """Determine if escrow requires compliance check"""
        # High-value escrows or disputed escrows need compliance
        return (self.amount > Decimal('10000') or 
                self.dispute_status != 'none' or
                self.requires_compliance_approval)


class EscrowLog(models.Model):
    """
    Audit log for escrow actions
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('viewed', 'Viewed'),
        ('updated', 'Updated'),
        ('funded', 'Funded'),
        ('released', 'Released'),
        ('disputed', 'Disputed'),
        ('compliance_requested', 'Compliance Requested'),  # NEW
        ('compliance_approved', 'Compliance Approved'),    # NEW
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    escrow = models.ForeignKey(Escrow, on_delete=models.CASCADE, related_name='logs')
    user_id = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} | {self.escrow.escrow_id}"