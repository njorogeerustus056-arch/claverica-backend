"""
compliance/models.py - CENTRAL COMPLIANCE SYSTEM FOR ALL APPS
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

# DO NOT call get_user_model() at module level - use string references instead

def generate_compliance_id():
    """Generate a unique compliance ID"""
    return f"COMP{uuid.uuid4().hex[:12].upper()}"


def generate_kyc_id():
    """Generate a unique KYC ID"""
    return f"KYC{uuid.uuid4().hex[:12].upper()}"


def generate_document_id():
    """Generate a unique document ID"""
    return f"DOC{uuid.uuid4().hex[:12].upper()}"


def generate_tac_id():
    """Generate a unique TAC ID"""
    return f"TAC{uuid.uuid4().hex[:12].upper()}"


def generate_session_id():
    """Generate a unique session ID"""
    return f"VID{uuid.uuid4().hex[:12].upper()}"


def generate_log_id():
    """Generate a unique audit log ID"""
    return f"AUD{uuid.uuid4().hex[:12].upper()}"


def generate_rule_id():
    """Generate a unique rule ID"""
    return f"RULE{uuid.uuid4().hex[:12].upper()}"


def generate_alert_id():
    """Generate a unique alert ID"""
    return f"ALT{uuid.uuid4().hex[:12].upper()}"


# ADD THIS MISSING MODEL

    class Meta:
        app_label = 'compliance'
class ComplianceProfile(models.Model):
    """Compliance profile for users"""
    user = models.OneToOneField('accounts.Account', on_delete=models.CASCADE, related_name='compliance_profile', null=True, blank=True)
    kyc_status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])
    risk_level = models.CharField(max_length=20, default='low', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
    last_kyc_date = models.DateTimeField(null=True, blank=True)
    next_kyc_review = models.DateTimeField(null=True, blank=True)
    restrictions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    

    class Meta:
        app_label = 'compliance'
        db_table = "compliance_profiles"
        db_table = 'compliance_profiles'
    def __str__(self):
        return f"Compliance Profile for {self.user.email}"
class ComplianceRequest(models.Model):
    """Central model for all compliance requests across apps"""
    
    APPS = [
        ('payments', 'Payments App'),
        ('escrow', 'Escrow App'),
        ('crypto', 'Crypto App'),
        ('wallet', 'Wallet System'),
        ('loan', 'Loan App'),
        ('investment', 'Investment App'),
    ]
    
    REQUEST_TYPES = [
        ('manual_payment', 'Manual Payment Release'),
        ('kyc_verification', 'KYC Verification'),
        ('withdrawal_approval', 'Withdrawal Approval'),
        ('deposit_verification', 'Deposit Verification'),
        ('transaction_limit', 'Transaction Limit Increase'),
        ('account_verification', 'Account Verification'),
        ('document_verification', 'Document Verification'),
        ('risk_review', 'Risk Review'),
        ('sanctions_check', 'Sanctions Check'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('info_required', 'Additional Info Required'),
        ('kyc_requested', 'KYC Form Requested'),
        ('video_call_scheduled', 'Video Call Scheduled'),
        ('awaiting_tac', 'Awaiting TAC Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core identifiers
    compliance_id = models.CharField(max_length=100, default=generate_compliance_id)
    app_name = models.CharField(max_length=50, choices=APPS, default="")
    app_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # User information - using string reference
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='compliance_requests', null=True, blank=True)
    user_email = models.EmailField()
    user_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Request details
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES, default="")
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, default='normal', choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ])
    
    # Compliance workflow
    requires_kyc = models.BooleanField(default=False)
    requires_video_call = models.BooleanField(default=False)
    requires_tac = models.BooleanField(default=False)
    requires_manual_review = models.BooleanField(default=False)
    
    # Risk assessment
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, default='low', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ])
    
    # KYC reference (if KYC is involved)
    kyc_verification = models.ForeignKey(
        'KYCVerification',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compliance_requests'
    )
    
    # TAC reference
    tac_code = models.CharField(max_length=10, blank=True, null=True)
    tac_generated_at = models.DateTimeField(null=True, blank=True)
    tac_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Video call details
    video_call_scheduled_at = models.DateTimeField(null=True, blank=True)
    video_call_link = models.URLField(blank=True, null=True)
    video_call_completed_at = models.DateTimeField(null=True, blank=True)
    video_call_duration = models.IntegerField(null=True, blank=True)  # in minutes
    video_call_notes = models.TextField(blank=True, null=True)
    
    # Review process
    assigned_to = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_compliance_requests'
    )
    reviewed_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_compliance_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    
    # Form data and documents
    form_data = models.JSONField(default=dict, blank=True)
    documents = models.JSONField(default=list, blank=True)
    
    # Decisions
    decision = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('pending', 'Pending'),
        ('escalate', 'Escalate'),
    ])
    decision_reason = models.TextField(blank=True, null=True)
    decision_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'compliance_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['compliance_id']),
            models.Index(fields=['app_name', 'app_transaction_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.compliance_id} - {self.app_name} - {self.request_type} - {self.status}"
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def time_since_creation(self):
        return timezone.now() - self.created_at


class KYCVerification(models.Model):
    """Central KYC verification for all users across all apps"""
    
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    COMPLIANCE_LEVELS = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('enhanced', 'Enhanced'),
        ('premium', 'Premium'),
    ]
    
    DOCUMENT_TYPES = [
        ('passport', 'Passport'),
        ('national_id', 'National ID'),
        ('drivers_license', "Driver's License"),
        ('utility_bill', 'Utility Bill'),
        ('bank_statement', 'Bank Statement'),
        ('proof_of_address', 'Proof of Address'),
        ('selfie', 'Selfie with ID'),
        ('tax_document', 'Tax Document'),
        ('incorporation_certificate', 'Incorporation Certificate'),
        ('business_license', 'Business License'),
    ]
    
    # Core identifiers
    kyc_id = models.CharField(max_length=100, default=generate_kyc_id)
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='kyc_verifications', null=True, blank=True)
    
    # Personal Information
    first_name = models.CharField(max_length=100, default="")
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, default="")
    date_of_birth = models.DateField( null=True, blank=True)
    nationality = models.CharField(max_length=100, default="")
    country_of_residence = models.CharField(max_length=100, default="")
    country_of_birth = models.CharField(max_length=100, blank=True, null=True)
    
    # Contact Information
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, default="")
    address_line1 = models.CharField(max_length=255, default="")
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, default="")
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, default="")
    
    # Identity Information
    id_number = models.CharField(max_length=100, default="")
    id_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES, default="")
    id_issue_date = models.DateField(null=True, blank=True)
    id_expiry_date = models.DateField(null=True, blank=True)
    id_issuing_country = models.CharField(max_length=100, blank=True, null=True)
    
    # Business Information (for corporate KYC)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_registration_number = models.CharField(max_length=100, blank=True, null=True)
    business_nature = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Employment Information
    occupation = models.CharField(max_length=100, blank=True, null=True)
    employer_name = models.CharField(max_length=255, blank=True, null=True)
    employment_status = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('employed', 'Employed'),
        ('self_employed', 'Self-Employed'),
        ('unemployed', 'Unemployed'),
        ('student', 'Student'),
        ('retired', 'Retired'),
    ])
    
    # Financial Information
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    income_currency = models.CharField(max_length=3, default='USD')
    source_of_funds = models.TextField(blank=True, null=True)
    expected_monthly_volume = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purpose_of_account = models.TextField(blank=True, null=True)
    
    # Verification Status
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    compliance_level = models.CharField(max_length=20, choices=COMPLIANCE_LEVELS, default='basic')
    
    # Risk Assessment
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, default='low')
    risk_factors = models.JSONField(default=list, blank=True)
    pep_status = models.BooleanField(default=False)
    pep_details = models.TextField(blank=True, null=True)
    sanctions_match = models.BooleanField(default=False)
    sanctions_details = models.JSONField(default=dict, blank=True)
    
    # Review Process
    submitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    verified_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_kyc_records'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Documents (references to document table)
    documents_submitted = models.IntegerField(default=0)
    documents_approved = models.IntegerField(default=0)
    documents_rejected = models.IntegerField(default=0)
    
    # Compliance Checks
    pep_check_completed = models.BooleanField(default=False)
    sanctions_check_completed = models.BooleanField(default=False)
    adverse_media_check_completed = models.BooleanField(default=False)
    document_verification_completed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    next_review_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'kyc_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['kyc_id']),
            models.Index(fields=['user', 'verification_status']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.kyc_id} - {self.first_name} {self.last_name} - {self.verification_status}"
    
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        return None
    
    def is_expired(self):
        if self.id_expiry_date:
            return timezone.now().date() > self.id_expiry_date
        return False


class KYCDocument(models.Model):
    """Documents submitted for KYC verification"""
    
    DOCUMENT_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    # Core identifiers
    document_id = models.CharField(max_length=100, default=generate_document_id)
    kyc_verification = models.ForeignKey(
        KYCVerification,
        on_delete=models.CASCADE,
        related_name='documents'
    , null=True, blank=True)
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='kyc_documents', null=True, blank=True)
    
    # Document Information
    document_type = models.CharField(max_length=50, choices=KYCVerification.DOCUMENT_TYPES, default="")
    document_number = models.CharField(max_length=100, blank=True, null=True)
    document_name = models.CharField(max_length=255, default="Unnamed Document")
    
    # File Information
    file_name = models.CharField(max_length=255, default="")
    original_file_name = models.CharField(max_length=255, default="")
    file_path = models.CharField(max_length=500, default="")
    file_url = models.URLField(blank=True, null=True)
    file_size = models.IntegerField( default=0)  # in bytes
    file_type = models.CharField(max_length=100, default="")
    file_hash = models.CharField(max_length=64, blank=True, null=True)
    
    # Document Details
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    issuing_country = models.CharField(max_length=100, blank=True, null=True)
    issuing_authority = models.CharField(max_length=255, blank=True, null=True)
    
    # Verification Status
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='pending')
    verified_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('manual', 'Manual Review'),
        ('automated', 'Automated Check'),
        ('third_party', 'Third Party Service'),
    ])
    
    # OCR & Data Extraction
    ocr_data = models.JSONField(default=dict, blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Notes and Rejection
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Security
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'kyc_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['kyc_verification', 'document_type']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.document_id} - {self.document_type} - {self.status}"
    
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False


class TACRequest(models.Model):
    """Transaction Authorization Code requests"""
    
    TAC_TYPES = [
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
        ('account_change', 'Account Change'),
        ('security', 'Security'),
    ]
    
    # Core identifiers
    tac_id = models.CharField(max_length=100, default=generate_tac_id)
    compliance_request = models.ForeignKey(
        ComplianceRequest,
        on_delete=models.CASCADE,
        related_name='tac_requests',
        null=True,
        blank=True
    )
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='tac_requests', null=True, blank=True)
    
    # TAC Details
    tac_code = models.CharField(max_length=10, default="")
    tac_type = models.CharField(max_length=30, choices=TAC_TYPES, default='withdrawal')
    purpose = models.TextField(blank=True, null=True)
    
    # Status
    is_used = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Transaction Details
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Delivery
    sent_via = models.CharField(max_length=50, default='email', choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
    ])
    sent_to = models.CharField(max_length=255, default="")
    delivery_status = models.CharField(max_length=50, default='pending', choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ])
    delivery_attempts = models.IntegerField(default=0)
    
    # Verification
    verified_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_tacs'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_ip = models.GenericIPAddressField(null=True, blank=True)
    verification_user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    expires_at = models.DateTimeField( null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Security
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'tac_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tac_id']),
            models.Index(fields=['user', 'is_used', 'is_expired']),
            models.Index(fields=['tac_code']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.tac_id} - {self.tac_type} - {'Used' if self.is_used else 'Active'}"
    
    def is_valid(self):
        return not self.is_used and not self.is_expired and timezone.now() < self.expires_at
    
    def time_remaining(self):
        if self.expires_at:
            remaining = self.expires_at - timezone.now()
            return max(0, remaining.total_seconds())
        return 0


class VideoCallSession(models.Model):
    """Video call sessions for compliance verification"""
    
    SESSION_STATUS = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    # Core identifiers
    session_id = models.CharField(max_length=100, default=generate_session_id)
    compliance_request = models.ForeignKey(
        ComplianceRequest,
        on_delete=models.CASCADE,
        related_name='video_calls'
    )
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='video_calls', null=True, blank=True)
    
    # Session Details
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='scheduled')
    purpose = models.TextField(blank=True, null=True)
    scheduled_for = models.DateTimeField( null=True, blank=True)
    duration_minutes = models.IntegerField(default=30)
    
    # Participants
    agent = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agent_video_calls'
    )
    agent_name = models.CharField(max_length=255, blank=True, null=True)
    agent_title = models.CharField(max_length=100, blank=True, null=True)
    
    # Video Call Platform
    platform = models.CharField(max_length=50, default='zoom', choices=[
        ('zoom', 'Zoom'),
        ('google_meet', 'Google Meet'),
        ('microsoft_teams', 'Microsoft Teams'),
        ('custom', 'Custom Platform'),
    ])
    meeting_link = models.URLField()
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    meeting_password = models.CharField(max_length=100, blank=True, null=True)
    
    # Session Data
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    actual_duration = models.IntegerField(null=True, blank=True)  # in minutes
    
    # Recording
    is_recorded = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True, null=True)
    recording_duration = models.IntegerField(null=True, blank=True)
    transcription = models.TextField(blank=True, null=True)
    
    # Verification Outcome
    verification_passed = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)
    issues_identified = models.JSONField(default=list, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True, null=True)
    
    # Security
    ip_address_user = models.GenericIPAddressField(null=True, blank=True)
    ip_address_agent = models.GenericIPAddressField(null=True, blank=True)
    
    # Notifications
    user_notified = models.BooleanField(default=False)
    agent_notified = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'video_call_sessions'
        ordering = ['scheduled_for']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['compliance_request']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['status', 'scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.session_id} - {self.user.email} - {self.status}"
    
    def is_upcoming(self):
        return self.status in ['scheduled', 'rescheduled'] and timezone.now() < self.scheduled_for
    
    def time_until_session(self):
        if self.scheduled_for:
            return self.scheduled_for - timezone.now()
        return None


class ComplianceAuditLog(models.Model):
    """Audit log for all compliance actions"""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('verify', 'Verify'),
        ('escalate', 'Escalate'),
        ('comment', 'Comment'),
        ('view', 'View'),
    ]
    
    ENTITY_TYPES = [
        ('compliance_request', 'Compliance Request'),
        ('kyc_verification', 'KYC Verification'),
        ('kyc_document', 'KYC Document'),
        ('tac_request', 'TAC Request'),
        ('video_call', 'Video Call'),
        ('user', 'User'),
        ('transaction', 'Transaction'),
    ]
    
    # Core identifiers
    log_id = models.CharField(max_length=100, default=generate_log_id)
    
    # Entity Information
    entity_type = models.CharField(max_length=50, choices=ENTITY_TYPES, default="")
    entity_id = models.CharField(max_length=100, default="")
    
    # Action Information
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, default="")
    action_description = models.TextField( default="No description provided", blank=True)
    
    # User Information
    user = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='compliance_audit_logs')
    user_email = models.EmailField(blank=True, null=True)
    user_role = models.CharField(max_length=50, blank=True, null=True)
    
    # Changes
    old_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # Related Data
    compliance_request = models.ForeignKey(
        ComplianceRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    kyc_verification = models.ForeignKey(
        KYCVerification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    class Meta:
        db_table = 'compliance_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['log_id']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['compliance_request', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.log_id} - {self.entity_type} - {self.action_type}"


class ComplianceRule(models.Model):
    """Compliance rules and thresholds"""
    
    RULE_TYPES = [
        ('amount_limit', 'Amount Limit'),
        ('frequency_limit', 'Frequency Limit'),
        ('velocity_limit', 'Velocity Limit'),
        ('geographic_restriction', 'Geographic Restriction'),
        ('document_requirement', 'Document Requirement'),
        ('risk_threshold', 'Risk Threshold'),
        ('kyc_requirement', 'KYC Requirement'),
        ('sanctions_check', 'Sanctions Check'),
    ]
    
    APPLICABLE_APPS = [
        ('all', 'All Apps'),
        ('payments', 'Payments Only'),
        ('escrow', 'Escrow Only'),
        ('crypto', 'Crypto Only'),
        ('wallet', 'Wallet Only'),
        ('loan', 'Loan Only'),
        ('investment', 'Investment Only'),
    ]
    
    # Core identifiers
    rule_id = models.CharField(max_length=100, default=generate_rule_id)
    rule_name = models.CharField(max_length=255, default="")
    rule_description = models.TextField( default="")
    
    # Rule Configuration
    rule_type = models.CharField(max_length=50, choices=RULE_TYPES, default="")
    applicable_apps = models.CharField(max_length=50, choices=APPLICABLE_APPS, default='all')
    priority = models.IntegerField(default=1)
    
    # Conditions
    condition = models.JSONField(default=dict, blank=True)
    threshold_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    threshold_currency = models.CharField(max_length=3, default='USD')
    time_period = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('per_transaction', 'Per Transaction'),
    ])
    
    # Actions
    action = models.CharField(max_length=50, choices=[
        ('allow', 'Allow'),
        ('deny', 'Deny'),
        ('review', 'Require Review'),
        ('escalate', 'Escalate'),
        ('notify', 'Notify'),
        ('limit', 'Apply Limit'),
    ], default="")
    action_details = models.JSONField(default=dict, blank=True)
    
    # Risk Parameters
    risk_weight = models.FloatField(default=1.0)
    risk_multiplier = models.FloatField(default=1.0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_automated = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey('accounts.Account', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    effective_from = models.DateTimeField( null=True, blank=True)
    effective_to = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'compliance_rules'
        ordering = ['priority', 'rule_name']
        indexes = [
            models.Index(fields=['rule_id']),
            models.Index(fields=['rule_type', 'is_active']),
            models.Index(fields=['applicable_apps', 'is_active']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.rule_id} - {self.rule_name}"
    
    def is_effective(self):
        now = timezone.now()
        if self.effective_to:
            return self.effective_from <= now <= self.effective_to
        return self.effective_from <= now


class ComplianceAlert(models.Model):
    """Compliance alerts and notifications"""
    
    ALERT_TYPES = [
        ('risk_threshold', 'Risk Threshold Exceeded'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('rule_violation', 'Rule Violation'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('kyc_expiring', 'KYC Expiring Soon'),
        ('document_expiring', 'Document Expiring Soon'),
        ('unusual_pattern', 'Unusual Pattern Detected'),
        ('sanctions_match', 'Sanctions Match'),
        ('pep_identified', 'PEP Identified'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    # Core identifiers
    alert_id = models.CharField(max_length=100, default=generate_alert_id)
    
    # Alert Details
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES, default="")
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='warning')
    title = models.CharField(max_length=255, default="")
    description = models.TextField( default="")
    
    # Related Entities
    compliance_request = models.ForeignKey(
        ComplianceRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    kyc_verification = models.ForeignKey(
        KYCVerification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='compliance_alerts'
    )
    
    # Alert Data
    alert_data = models.JSONField(default=dict, blank=True)
    trigger_conditions = models.JSONField(default=dict, blank=True)
    
    # Status
    is_resolved = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Notification
    notified_users = models.JSONField(default=list, blank=True)
    notification_sent = models.BooleanField(default=False)
    notification_channels = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'compliance_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_id']),
            models.Index(fields=['alert_type', 'is_resolved']),
            models.Index(fields=['severity', 'created_at']),
            models.Index(fields=['is_resolved', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_id} - {self.alert_type} - {self.severity}"
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class ComplianceDashboardStats(models.Model):
    """Aggregated statistics for compliance dashboard"""
    
    # Time period
    period_type = models.CharField(max_length=20, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    period_start = models.DateTimeField( null=True, blank=True)
    period_end = models.DateTimeField( null=True, blank=True)
    
    # Request Statistics
    total_requests = models.IntegerField(default=0)
    pending_requests = models.IntegerField(default=0)
    approved_requests = models.IntegerField(default=0)
    rejected_requests = models.IntegerField(default=0)
    escalated_requests = models.IntegerField(default=0)
    
    # KYC Statistics
    kyc_submissions = models.IntegerField(default=0)
    kyc_approved = models.IntegerField(default=0)
    kyc_rejected = models.IntegerField(default=0)
    kyc_pending = models.IntegerField(default=0)
    
    # TAC Statistics
    tac_generated = models.IntegerField(default=0)
    tac_verified = models.IntegerField(default=0)
    tac_expired = models.IntegerField(default=0)
    tac_failed = models.IntegerField(default=0)
    
    # Video Call Statistics
    video_calls_scheduled = models.IntegerField(default=0)
    video_calls_completed = models.IntegerField(default=0)
    video_calls_cancelled = models.IntegerField(default=0)
    video_call_success_rate = models.FloatField(default=0.0)
    
    # Risk Statistics
    high_risk_count = models.IntegerField(default=0)
    medium_risk_count = models.IntegerField(default=0)
    low_risk_count = models.IntegerField(default=0)
    average_risk_score = models.FloatField(default=0.0)
    
    # Processing Time
    avg_processing_time_hours = models.FloatField(default=0.0)
    median_processing_time_hours = models.FloatField(default=0.0)
    p90_processing_time_hours = models.FloatField(default=0.0)
    
    # App-specific Statistics
    payments_requests = models.IntegerField(default=0)
    escrow_requests = models.IntegerField(default=0)
    crypto_requests = models.IntegerField(default=0)
    wallet_requests = models.IntegerField(default=0)
    
    # Compliance Officer Statistics
    requests_per_officer = models.JSONField(default=dict, blank=True)
    avg_resolution_time_per_officer = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'compliance_dashboard_stats'
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['period_type', 'period_end']),
            models.Index(fields=['period_end']),
        ]
        unique_together = ['period_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"Stats {self.period_type} - {self.period_start.date()} to {self.period_end.date()}"