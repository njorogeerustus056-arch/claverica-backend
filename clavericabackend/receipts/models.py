from django.db import models
from django.contrib.auth.models import User
import uuid

class Receipt(models.Model):
    """
    Receipt model for storing user receipt metadata
    """
    CATEGORY_CHOICES = [
        ('business', 'Business Expense'),
        ('personal', 'Personal Expense'),
        ('travel', 'Travel'),
        ('entertainment', 'Entertainment'),
        ('food', 'Food & Dining'),
        ('utilities', 'Utilities'),
        ('shopping', 'Shopping'),
        ('healthcare', 'Healthcare'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    file_name = models.CharField(max_length=255)
    original_file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="Size in bytes")
    file_type = models.CharField(max_length=100)
    storage_path = models.CharField(max_length=500)
    
    # Receipt details
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='USD')
    transaction_date = models.DateTimeField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    notes = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user_id', '-uploaded_at']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.original_file_name} - {self.user_id}"
    
    @property
    def file_size_mb(self):
        """Returns file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
