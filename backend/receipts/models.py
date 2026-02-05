from django.db import models
from accounts.models import Account

class Receipt(models.Model):
    # File upload fields
    file = models.CharField(max_length=100)
    original_file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Receipt data fields
    merchant_name = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    transaction_date = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=50, default='uncategorized')
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=dict)
    status = models.CharField(max_length=50, default='pending')
    
    # Metadata fields
    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    receipt_data = models.JSONField(default=dict)
    
    # Relationship fields
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='receipts')
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'uploaded_at']),
        ]
    
    def __str__(self):
        return f"Receipt #{self.id} - {self.user.email} (${self.amount})"
