from django.db import models
from django.utils import timezone
import json

class Escrow(models.Model):
    class Meta:
        app_label = "escrow"
    
    # Field 1-6: Basic identification
    escrow_id = models.CharField(max_length=50, default='ESCROW-7e953b90')
    sender_id = models.CharField(max_length=100, default='unknown')
    sender_name = models.CharField(max_length=255, default='Unknown Sender')
    receiver_id = models.CharField(max_length=100, default='unknown')
    receiver_name = models.CharField(max_length=255, default='Unknown Receiver')
    
    # Field 7-11: Financial
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Field 12-14: Description
    title = models.CharField(max_length=255, default='Untitled Escrow')
    description = models.TextField(default='No description')
    terms_and_conditions = models.TextField(blank=True, null=True)
    
    # Field 15: Status
    status = models.CharField(max_length=50, default='pending')
    
    # Field 16-18: Release flags
    is_released = models.BooleanField(default=False)
    release_approved_by_sender = models.BooleanField(default=False)
    release_approved_by_receiver = models.BooleanField(default=False)
    
    # Field 19-22: Dispute
    dispute_status = models.CharField(max_length=50, default='', blank=True)
    dispute_reason = models.TextField(blank=True, null=True)
    dispute_opened_by = models.CharField(max_length=100, blank=True, null=True)
    dispute_opened_at = models.DateTimeField(blank=True, null=True)
    
    # Field 23-26: Timestamps
    expected_release_date = models.DateTimeField(blank=True, null=True)
    funded_at = models.DateTimeField(blank=True, null=True)
    released_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Field 27-30: Metadata and compliance
    metadata = models.JSONField(default=dict)
    compliance_reference = models.CharField(max_length=100, blank=True, null=True)
    requires_compliance_approval = models.BooleanField(default=False)
    name = models.CharField(max_length=255, default='Escrow')
    
    def __str__(self):
        return f"{self.title} ({self.escrow_id})"

class EscrowLog(models.Model):
    class Meta:
        app_label = "escrow"
    
    escrow = models.ForeignKey(Escrow, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Log: {self.escrow.title} - {self.action}"
