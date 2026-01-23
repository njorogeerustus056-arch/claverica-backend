from django.db import models
import uuid

class Escrow(models.Model):
    # Complete database schema
    escrow_id = models.CharField(max_length=100, blank=True, null=True)
    sender_id = models.CharField(max_length=255, default='unknown')
    sender_name = models.CharField(max_length=255, default='Unknown Sender')
    receiver_id = models.CharField(max_length=255, default='unknown')
    receiver_name = models.CharField(max_length=255, default='Unknown Receiver')
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    currency = models.CharField(max_length=3, default='USD')
    fee = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='pending')
    is_released = models.BooleanField(default=False)
    release_approved_by_sender = models.BooleanField(default=False)
    release_approved_by_receiver = models.BooleanField(default=False)
    dispute_status = models.CharField(max_length=50, default='none')
    dispute_reason = models.TextField(blank=True, null=True)
    dispute_opened_by = models.CharField(max_length=255, blank=True, null=True)
    dispute_opened_at = models.DateTimeField(blank=True, null=True)
    expected_release_date = models.DateTimeField(blank=True, null=True)
    funded_at = models.DateTimeField(blank=True, null=True)
    released_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)
    compliance_reference = models.CharField(max_length=255, blank=True, null=True)
    requires_compliance_approval = models.BooleanField(default=False)
    name = models.CharField(max_length=255, default='')
    
    class Meta:
        db_table = 'escrow_escrow'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.escrow_id or 'ESCROW'} - {self.name} (${self.amount})"
    
    def save(self, *args, **kwargs):
        if not self.escrow_id:
            self.escrow_id = f"ESCROW-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
