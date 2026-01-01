"""
compliance/models.py
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class VerificationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_REVIEW = 'in_review', 'In Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    EXPIRED = 'expired', 'Expired'


class DocumentType(models.TextChoices):
    PASSPORT = 'passport', 'Passport'
    NATIONAL_ID = 'national_id', 'National ID'
    DRIVERS_LICENSE = 'drivers_license', "Driver's License"
    UTILITY_BILL = 'utility_bill', 'Utility Bill'
    BANK_STATEMENT = 'bank_statement', 'Bank Statement'
    SELFIE = 'selfie', 'Selfie'


class ComplianceLevel(models.TextChoices):
    BASIC = 'basic', 'Basic'
    STANDARD = 'standard', 'Standard'
    ENHANCED = 'enhanced', 'Enhanced'
    PREMIUM = 'premium', 'Premium'


class KYCVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateTimeField()
    nationality = models.CharField(max_length=100)
    country_of_residence = models.CharField(max_length=100)
    
    # Contact Information
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    
    # Identity Verification
    id_number = models.CharField(max_length=100)
    id_type = models.CharField(max_length=20, choices=DocumentType.choices)
    id_issue_date = models.DateTimeField(blank=True, null=True)
    id_expiry_date = models.DateTimeField(blank=True, null=True)
    
    # Compliance Level
    compliance_level = models.CharField(
        max_length=20,
        choices=ComplianceLevel.choices,
        default=ComplianceLevel.BASIC
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    
    # Risk Assessment
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, default='low')
    
    # Verification Details
    verified_by = models.CharField(max_length=255, blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Additional Data
    occupation = models.CharField(max_length=100, blank=True, null=True)
    source_of_funds = models.CharField(max_length=255, blank=True, null=True)
    purpose_of_account = models.CharField(max_length=255, blank=True, null=True)
    expected_transaction_volume = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    geolocation = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.verification_status}"


class KYCDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(
        KYCVerification,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Document Details
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100, blank=True, null=True)
    
    # File Information
    file_name = models.CharField(max_length=255)
    original_file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=50)
    file_hash = models.CharField(max_length=64, blank=True, null=True)
    
    # Verification Status
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.CharField(max_length=255, blank=True, null=True)
    
    # OCR & Analysis
    ocr_data = models.JSONField(blank=True, null=True)
    extracted_data = models.JSONField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kyc_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['verification']),
        ]
    
    def __str__(self):
        return f"{self.document_type} - {self.original_file_name}"


class ComplianceCheck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    verification = models.ForeignKey(
        KYCVerification,
        on_delete=models.CASCADE,
        related_name='compliance_checks'
    )
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Check Details
    check_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    result = models.JSONField(blank=True, null=True)
    
    # Risk Information
    risk_score = models.FloatField(default=0.0)
    matches_found = models.IntegerField(default=0)
    
    # Provider Information
    provider = models.CharField(max_length=100, blank=True, null=True)
    provider_reference = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    checked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'compliance_checks'
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"{self.check_type} - {self.status}"


class TACCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Code Details
    code = models.CharField(max_length=6)
    code_type = models.CharField(max_length=20, default='withdrawal')
    
    # Validation
    is_used = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Associated Data
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.FloatField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    
    # IP & Security
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'tac_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'is_used', 'is_expired']),
        ]
    
    def __str__(self):
        return f"TAC {self.code} - {self.user_id}"


class ComplianceAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    verification_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Action Details
    action = models.CharField(max_length=255)
    action_type = models.CharField(max_length=50)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=255)
    
    # Changes
    old_value = models.JSONField(blank=True, null=True)
    new_value = models.JSONField(blank=True, null=True)
    
    # Actor Information
    actor_id = models.CharField(max_length=255, blank=True, null=True)
    actor_role = models.CharField(max_length=50, blank=True, null=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'compliance_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.created_at}"


class WithdrawalRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, db_index=True)
    
    # Amount Details
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default='USD')
    
    # Destination
    destination_type = models.CharField(max_length=50)
    destination_details = models.JSONField()
    
    # Status
    status = models.CharField(max_length=20, default='pending')
    
    # Compliance
    requires_tac = models.BooleanField(default=True)
    tac_verified = models.BooleanField(default=False)
    tac_code_id = models.CharField(max_length=255, blank=True, null=True)
    
    kyc_status = models.CharField(max_length=20, blank=True, null=True)
    compliance_status = models.CharField(max_length=20, default='pending')
    
    # Processing
    processed_by = models.CharField(max_length=255, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    transaction_hash = models.CharField(max_length=255, blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Withdrawal {self.amount} {self.currency} - {self.status}"