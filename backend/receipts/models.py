from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os

User = get_user_model()

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')  # CHANGED: Use ForeignKey
    file = models.FileField(upload_to='receipts/%Y/%m/%d/')  # ADDED: File field
    
    # File metadata
    original_file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="Size in bytes")
    file_type = models.CharField(max_length=100)
    
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
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.original_file_name} - {self.user.email}"
    
    @property
    def file_size_mb(self):
        """Returns file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0
    
    def save(self, *args, **kwargs):
        # Set file metadata if file is provided
        if self.file and not self.original_file_name:
            self.original_file_name = self.file.name
        
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        if self.file and not self.file_type:
            # FIXED: Handle content_type attribute safely
            try:
                # Try to get content_type from the file object
                if hasattr(self.file, 'content_type'):
                    self.file_type = self.file.content_type
                else:
                    # Fallback: determine from file extension
                    filename = self.file.name
                    extension = os.path.splitext(filename)[1].lower()
                    
                    # Map extensions to content types
                    extension_map = {
                        '.txt': 'text/plain',
                        '.pdf': 'application/pdf',
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.doc': 'application/msword',
                        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        '.xls': 'application/vnd.ms-excel',
                        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    }
                    
                    self.file_type = extension_map.get(extension, 'application/octet-stream')
            except (AttributeError, KeyError):
                # Final fallback
                self.file_type = 'application/octet-stream'
            
        super().save(*args, **kwargs)