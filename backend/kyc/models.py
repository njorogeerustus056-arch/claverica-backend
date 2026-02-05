from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone

class KYCDocument(models.Model):
    """Stores KYC documents for verification"""
    
    DOCUMENT_TYPES = [
        ('national_id', 'National ID Card'),
        ('driver_license', 'Driver License'),
        ('passport', 'Passport'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_correction', 'Needs Correction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_documents')
    
    # Document Type
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='national_id')
    
    # Document Images
    id_front_image = models.ImageField(upload_to='kyc/id_front/%Y/%m/%d/', verbose_name='ID Front')
    id_back_image = models.ImageField(upload_to='kyc/id_back/%Y/%m/%d/', verbose_name='ID Back', null=True, blank=True)
    facial_image = models.ImageField(upload_to='kyc/facial/%Y/%m/%d/', verbose_name='Facial Verification')
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin Review Fields
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='reviewed_kyc_documents')
    admin_notes = models.TextField(blank=True, verbose_name='Review Notes')
    rejection_reason = models.TextField(blank=True, verbose_name='Reason for Rejection/Correction')
    
    # Auto-expire pending submissions after 30 days
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "kyc_documents"
        app_label = "kyc"
        ordering = ['-submitted_at']
        verbose_name = "KYC Document"
        verbose_name_plural = "KYC Documents"
    
    def __str__(self):
        return f"KYC for {self.user.email} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Set expiration date for new pending submissions"""
        if not self.pk and self.status == 'pending':
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if submission has expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False
    
    @property
    def is_approved(self):
        """Check if KYC is approved"""
        return self.status == 'approved'

class KYCSubmission(models.Model):
    """Tracks KYC submission requests and status"""
    
    SERVICE_TYPES = [
        ('transfer', 'Large Transfer'),
        ('loan', 'Loan Application'),
        ('escrow', 'Escrow Service'),
        ('savings', 'Savings Account'),
        ('crypto', 'Crypto Services'),
        ('card', 'Virtual Card'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_submissions')
    
    # What triggered this KYC request
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)
    requested_for = models.CharField(max_length=255, help_text="What service/feature requires KYC")
    
    # Linked document
    kyc_document = models.OneToOneField(KYCDocument, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Threshold that triggered this (for transfers)
    amount_triggered = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    threshold_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = "kyc_submissions"
        app_label = "kyc"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"KYC Submission for {self.user.email} - {self.get_service_type_display()}"

class KYCSetting(models.Model):
    """Configurable KYC settings and thresholds"""
    
    service_type = models.CharField(max_length=50, choices=KYCSubmission.SERVICE_TYPES, unique=True)
    requires_kyc = models.BooleanField(default=True)
    threshold_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1500.00,
                                          help_text="Amount above which KYC is required")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "kyc_settings"
        app_label = "kyc"
        verbose_name = "KYC Setting"
        verbose_name_plural = "KYC Settings"
    
    def __str__(self):
        return f"{self.get_service_type_display()} - "
