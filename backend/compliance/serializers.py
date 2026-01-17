"""
compliance/serializers.py - Django REST Framework serializers for central compliance app
"""

import logging
from typing import Dict, Any, Optional
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

from .models import (
    ComplianceRequest, KYCVerification, KYCDocument,
    TACRequest, VideoCallSession, ComplianceAuditLog,
    ComplianceRule, ComplianceDashboardStats, ComplianceAlert,
    ComplianceProfile, ComplianceConfig
)

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = fields


class ComplianceProfileSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Profile model"""
    
    user = UserSerializer(read_only=True)
    compliance_status_display = serializers.CharField(source='get_compliance_status_display', read_only=True)
    kyc_status_display = serializers.CharField(source='get_kyc_status_display', read_only=True)
    
    # Calculated fields
    kyc_expires_soon = serializers.SerializerMethodField()
    days_until_kyc_expiry = serializers.SerializerMethodField()
    overall_compliance_score = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceProfile
        fields = [
            'id', 'user',
            
            # Counters
            'total_requests', 'approved_requests', 'rejected_requests',
            'pending_requests', 'escalated_requests',
            
            # Dates
            'last_request_date', 'last_approved_date', 'last_rejected_date',
            'created_at', 'updated_at',
            
            # KYC Information
            'kyc_verified', 'kyc_verification_date', 'kyc_expiry_date',
            'kyc_status', 'kyc_status_display',
            'kyc_expires_soon', 'days_until_kyc_expiry',
            
            # Compliance Information
            'compliance_level', 'compliance_status', 'compliance_status_display',
            'risk_score', 'risk_level',
            
            # Limits
            'daily_limit', 'monthly_limit', 'transaction_limit',
            'daily_used', 'monthly_used',
            
            # Verification Status
            'email_verified', 'phone_verified', 'id_verified',
            'address_verified', 'income_verified',
            
            # Flags
            'is_pep', 'is_sanctioned', 'has_adverse_media',
            'high_risk_country', 'restricted_occupation',
            
            # Metadata
            'metadata'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'kyc_expires_soon', 'days_until_kyc_expiry',
            'overall_compliance_score'
        ]
    
    def get_kyc_expires_soon(self, obj):
        """Check if KYC expires soon (within 30 days)"""
        return obj.kyc_expires_soon()
    
    def get_days_until_kyc_expiry(self, obj):
        """Get days until KYC expiry"""
        return obj.days_until_kyc_expiry()
    
    def get_overall_compliance_score(self, obj):
        """Calculate overall compliance score"""
        return obj.calculate_compliance_score()


class ComplianceConfigSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Configuration model"""
    
    config_type_display = serializers.CharField(source='get_config_type_display', read_only=True)
    
    class Meta:
        model = ComplianceConfig
        fields = [
            'id', 'config_type', 'config_type_display', 'config_name',
            'config_value', 'config_description', 'is_active',
            'applies_to', 'effective_from', 'effective_to',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceRequestSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Request model"""
    
    user = UserSerializer(read_only=True)
    user_email = serializers.EmailField(read_only=True)
    app_name_display = serializers.CharField(source='get_app_name_display', read_only=True)
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    decision_display = serializers.CharField(source='get_decision_display', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    
    # Calculated fields
    time_since_creation = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    processing_time_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceRequest
        fields = [
            'compliance_id', 'app_name', 'app_name_display', 'app_transaction_id',
            'user', 'user_email', 'user_phone',
            'request_type', 'request_type_display', 'amount', 'currency', 'description',
            'status', 'status_display', 'priority', 'priority_display',
            'requires_kyc', 'requires_video_call', 'requires_tac', 'requires_manual_review',
            'risk_score', 'risk_level', 'risk_level_display',
            'kyc_verification', 'tac_code', 'tac_generated_at', 'tac_verified_at',
            'video_call_scheduled_at', 'video_call_link', 'video_call_completed_at',
            'assigned_to', 'reviewed_by', 'reviewed_at', 'review_notes',
            'form_data', 'documents',
            'decision', 'decision_display', 'decision_reason', 'decision_notes',
            'time_since_creation', 'is_expired', 'processing_time_hours',
            'created_at', 'updated_at', 'resolved_at', 'expires_at',
            'ip_address', 'user_agent', 'metadata'
        ]
        read_only_fields = [
            'compliance_id', 'created_at', 'updated_at', 'time_since_creation',
            'is_expired', 'user', 'user_email', 'processing_time_hours'
        ]
    
    def get_time_since_creation(self, obj):
        """Calculate time since creation"""
        if obj.created_at:
            delta = timezone.now() - obj.created_at
            return str(delta).split('.')[0]  # Remove microseconds
        return None
    
    def get_is_expired(self, obj):
        """Check if request is expired"""
        return obj.is_expired()
    
    def get_processing_time_hours(self, obj):
        """Calculate processing time in hours"""
        if obj.resolved_at and obj.created_at:
            delta = obj.resolved_at - obj.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None


class ComplianceRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Compliance Requests"""
    
    class Meta:
        model = ComplianceRequest
        fields = [
            'app_name', 'app_transaction_id',
            'request_type', 'amount', 'currency', 'description',
            'form_data', 'documents', 'metadata'
        ]
    
    def validate(self, data):
        """Validate compliance request creation"""
        request = self.context.get('request')
        
        # Add current user to request
        if request and request.user:
            data['user'] = request.user
            data['user_email'] = request.user.email
            
            # Get user phone from profile if available
            try:
                from accounts.models import Profile
                profile = Profile.objects.get(user=request.user)
                if profile.phone_number:
                    data['user_phone'] = profile.phone_number
            except (Profile.DoesNotExist, ImportError):
                pass
        
        # Set default priority based on amount
        amount = data.get('amount', 0)
        if amount > 10000:
            data['priority'] = 'high'
        elif amount > 5000:
            data['priority'] = 'normal'
        else:
            data['priority'] = 'low'
        
        # Auto-detect requirements based on amount and type
        request_type = data.get('request_type')
        
        # Manual payments always require TAC and manual review
        if request_type == 'manual_payment':
            data['requires_tac'] = True
            data['requires_manual_review'] = True
        
        # Large amounts require KYC
        if amount > 5000:
            data['requires_kyc'] = True
        
        # Very large amounts require video call
        if amount > 10000:
            data['requires_video_call'] = True
        
        # Set initial risk score based on amount
        if amount > 0:
            data['risk_score'] = min(amount / 5000 * 10, 100)
            if data['risk_score'] > 70:
                data['risk_level'] = 'high'
            elif data['risk_score'] > 40:
                data['risk_level'] = 'medium'
            else:
                data['risk_level'] = 'low'
        
        # Set default expiry (24 hours for high priority, 72 for others)
        if data.get('priority') == 'high':
            data['expires_at'] = timezone.now() + timedelta(hours=24)
        else:
            data['expires_at'] = timezone.now() + timedelta(hours=72)
        
        return data
    
    def create(self, validated_data):
        """Create compliance request with compliance_id"""
        # Generate compliance_id if not provided
        if 'compliance_id' not in validated_data:
            validated_data['compliance_id'] = f"COMP-{uuid.uuid4().hex[:12].upper()}"
        
        return ComplianceRequest.objects.create(**validated_data)


class KYCVerificationSerializer(serializers.ModelSerializer):
    """Serializer for KYC Verification model"""
    
    user = UserSerializer(read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    compliance_level_display = serializers.CharField(source='get_compliance_level_display', read_only=True)
    id_type_display = serializers.CharField(source='get_id_type_display', read_only=True)
    employment_status_display = serializers.CharField(source='get_employment_status_display', read_only=True)
    
    # Calculated fields
    age = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_id_expired = serializers.SerializerMethodField()
    
    # Document counts
    documents_count = serializers.SerializerMethodField()
    documents_approved_count = serializers.SerializerMethodField()
    documents_pending_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCVerification
        fields = [
            'kyc_id', 'user',
            
            # Personal Information
            'first_name', 'middle_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'nationality', 'country_of_residence',
            'country_of_birth',
            
            # Contact Information
            'email', 'phone_number', 'address_line1', 'address_line2',
            'city', 'state_province', 'postal_code',
            
            # Identity Information
            'id_number', 'id_type', 'id_type_display', 'id_issue_date',
            'id_expiry_date', 'is_id_expired', 'id_issuing_country',
            
            # Business Information
            'company_name', 'company_registration_number', 'business_nature',
            'website',
            
            # Employment Information
            'occupation', 'employer_name', 'employment_status',
            'employment_status_display',
            
            # Financial Information
            'annual_income', 'income_currency', 'source_of_funds',
            'expected_monthly_volume', 'purpose_of_account',
            
            # Verification Status
            'verification_status', 'verification_status_display',
            'compliance_level', 'compliance_level_display',
            
            # Risk Assessment
            'risk_score', 'risk_level', 'risk_factors',
            'pep_status', 'pep_details', 'sanctions_match', 'sanctions_details',
            
            # Review Process
            'submitted_at', 'verified_by', 'verified_at', 'review_notes',
            'rejection_reason',
            
            # Document Information
            'documents_submitted', 'documents_approved', 'documents_rejected',
            'documents_count', 'documents_approved_count', 'documents_pending_count',
            
            # Compliance Checks
            'pep_check_completed', 'sanctions_check_completed',
            'adverse_media_check_completed', 'document_verification_completed',
            
            # Timestamps
            'created_at', 'updated_at', 'next_review_date',
            
            # Metadata
            'ip_address', 'user_agent', 'metadata'
        ]
        read_only_fields = [
            'kyc_id', 'created_at', 'updated_at', 'age', 'full_name',
            'is_id_expired', 'documents_count', 'documents_approved_count',
            'documents_pending_count', 'risk_score', 'risk_level'
        ]
    
    def get_age(self, obj):
        """Calculate age from date of birth"""
        return obj.age()
    
    def get_full_name(self, obj):
        """Get full name"""
        return obj.full_name()
    
    def get_is_id_expired(self, obj):
        """Check if ID is expired"""
        return obj.is_expired()
    
    def get_documents_count(self, obj):
        """Get total documents count"""
        return obj.documents.count()
    
    def get_documents_approved_count(self, obj):
        """Get approved documents count"""
        return obj.documents.filter(status='approved').count()
    
    def get_documents_pending_count(self, obj):
        """Get pending documents count"""
        return obj.documents.filter(status='pending').count()


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC Document model"""
    
    kyc_verification = KYCVerificationSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_method_display = serializers.CharField(source='get_verification_method_display', read_only=True)
    
    # Calculated fields
    file_size_mb = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    file_url_absolute = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCDocument
        fields = [
            'document_id', 'kyc_verification', 'user',
            
            # Document Information
            'document_type', 'document_type_display', 'document_number',
            'document_name',
            
            # File Information
            'file_name', 'original_file_name', 'file_path', 'file_url',
            'file_url_absolute', 'file_size', 'file_size_mb', 'file_type',
            'file_hash',
            
            # Document Details
            'issue_date', 'expiry_date', 'is_expired',
            'issuing_country', 'issuing_authority',
            
            # Verification Status
            'status', 'status_display', 'verified_by', 'verified_at',
            'verification_method', 'verification_method_display',
            
            # OCR & Data Extraction
            'ocr_data', 'extracted_data', 'confidence_score',
            
            # Notes and Rejection
            'notes', 'rejection_reason',
            
            # Security
            'is_encrypted', 'encryption_key',
            
            # Timestamps
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'document_id', 'file_name', 'file_path', 'file_size',
            'file_type', 'file_hash', 'uploaded_at', 'updated_at',
            'file_size_mb', 'is_expired', 'file_url_absolute'
        ]
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        return obj.file_size_mb()
    
    def get_is_expired(self, obj):
        """Check if document is expired"""
        return obj.is_expired()
    
    def get_file_url_absolute(self, obj):
        """Get absolute file URL"""
        request = self.context.get('request')
        if request and obj.file_url:
            return request.build_absolute_uri(obj.file_url)
        return obj.file_url


class KYCDocumentUploadSerializer(serializers.Serializer):
    """Serializer for KYC document upload"""
    
    kyc_verification_id = serializers.CharField()
    document_type = serializers.CharField()
    document_number = serializers.CharField(required=False, allow_blank=True)
    document_name = serializers.CharField()
    file = serializers.FileField()
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    issuing_country = serializers.CharField(required=False, allow_blank=True)
    issuing_authority = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate document upload"""
        # Check KYC verification exists and belongs to user
        request = self.context.get('request')
        if request and request.user:
            try:
                kyc = KYCVerification.objects.get(
                    kyc_id=data['kyc_verification_id'],
                    user=request.user
                )
                data['kyc_verification'] = kyc
                data['user'] = request.user
            except KYCVerification.DoesNotExist:
                raise serializers.ValidationError("KYC verification not found")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        file = data.get('file')
        if file and file.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB
        if file and file.size > max_size:
            raise serializers.ValidationError("File size exceeds 10MB limit")
        
        return data
    
    def create(self, validated_data):
        """Create KYC document"""
        file = validated_data.pop('file')
        
        # Generate unique filename
        import os
        from django.utils.text import get_valid_filename
        
        original_filename = get_valid_filename(file.name)
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Create document instance
        document = KYCDocument(
            **validated_data,
            original_file_name=original_filename,
            file_name=unique_filename,
            file_type=file.content_type,
            file_size=file.size
        )
        
        # Save file (implementation depends on your storage backend)
        # Example for FileSystemStorage:
        from django.core.files.storage import default_storage
        file_path = f"kyc_documents/{unique_filename}"
        document.file_path = file_path
        
        # Save file to storage
        default_storage.save(file_path, file)
        
        document.save()
        return document


class TACRequestSerializer(serializers.ModelSerializer):
    """Serializer for TAC Request model"""
    
    user = UserSerializer(read_only=True)
    compliance_request = ComplianceRequestSerializer(read_only=True)
    tac_type_display = serializers.CharField(source='get_tac_type_display', read_only=True)
    sent_via_display = serializers.CharField(source='get_sent_via_display', read_only=True)
    delivery_status_display = serializers.CharField(source='get_delivery_status_display', read_only=True)
    
    # Calculated fields
    is_valid = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    masked_sent_to = serializers.SerializerMethodField()
    
    class Meta:
        model = TACRequest
        fields = [
            'tac_id', 'compliance_request', 'user',
            
            # TAC Details
            'tac_code', 'tac_type', 'tac_type_display', 'purpose',
            
            # Status
            'is_used', 'is_expired', 'attempts', 'max_attempts',
            
            # Transaction Details
            'amount', 'currency', 'transaction_id',
            
            # Delivery
            'sent_via', 'sent_via_display', 'sent_to', 'masked_sent_to',
            'delivery_status', 'delivery_status_display', 'delivery_attempts',
            
            # Verification
            'verified_by', 'verified_at', 'verification_ip',
            'verification_user_agent',
            
            # Calculated fields
            'is_valid', 'time_remaining',
            
            # Timestamps
            'created_at', 'expires_at', 'used_at',
            
            # Security
            'ip_address', 'user_agent'
        ]
        read_only_fields = [
            'tac_id', 'tac_code', 'created_at', 'expires_at',
            'is_used', 'is_expired', 'attempts', 'verified_at',
            'is_valid', 'time_remaining', 'masked_sent_to'
        ]
    
    def get_is_valid(self, obj):
        """Check if TAC is valid"""
        return obj.is_valid()
    
    def get_time_remaining(self, obj):
        """Get time remaining in seconds"""
        return obj.time_remaining()
    
    def get_masked_sent_to(self, obj):
        """Mask the sent_to field for privacy"""
        if obj.sent_to:
            if '@' in obj.sent_to:  # Email
                parts = obj.sent_to.split('@')
                if len(parts) == 2:
                    username, domain = parts
                    if len(username) > 2:
                        masked = username[0] + '***' + username[-1] if len(username) > 4 else '***'
                        return f"{masked}@{domain}"
            elif len(obj.sent_to) > 6:  # Phone number
                return f"{obj.sent_to[:3]}***{obj.sent_to[-3:]}"
        return obj.sent_to


class TACGenerateSerializer(serializers.Serializer):
    """Serializer for TAC generation request"""
    
    compliance_request_id = serializers.CharField(required=False)
    user_id = serializers.CharField(required=False)
    tac_type = serializers.CharField(default='withdrawal')
    purpose = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    currency = serializers.CharField(default='USD')
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    sent_via = serializers.CharField(default='email')
    
    def validate(self, data):
        """Validate TAC generation"""
        request = self.context.get('request')
        
        # If user_id not provided, use current user
        if not data.get('user_id') and request and request.user:
            data['user_id'] = str(request.user.id)
        
        # Validate sent_via
        allowed_sent_via = ['email', 'sms', 'push', 'whatsapp', 'telegram']
        if data.get('sent_via') not in allowed_sent_via:
            raise serializers.ValidationError(
                f"Invalid sent_via. Allowed values: {', '.join(allowed_sent_via)}"
            )
        
        return data
    
    def create(self, validated_data):
        """Create TAC request"""
        from .services import generate_tac
        
        return generate_tac(**validated_data)


class TACVerifySerializer(serializers.Serializer):
    """Serializer for TAC verification"""
    
    tac_id = serializers.CharField(required=False)
    tac_code = serializers.CharField()
    compliance_request_id = serializers.CharField(required=False)
    
    def validate(self, data):
        """Validate TAC verification"""
        # At least one identifier must be provided
        if not data.get('tac_id') and not data.get('compliance_request_id'):
            raise serializers.ValidationError(
                "Either tac_id or compliance_request_id must be provided"
            )
        
        # Validate TAC code format
        tac_code = data.get('tac_code')
        if not tac_code or len(tac_code) != 6 or not tac_code.isdigit():
            raise serializers.ValidationError("TAC code must be 6 digits")
        
        return data
    
    def verify(self):
        """Verify TAC code"""
        from .services import verify_tac
        
        tac_id = self.validated_data.get('tac_id')
        tac_code = self.validated_data.get('tac_code')
        compliance_request_id = self.validated_data.get('compliance_request_id')
        
        return verify_tac(tac_code, tac_id, compliance_request_id)


class VideoCallSessionSerializer(serializers.ModelSerializer):
    """Serializer for Video Call Session model"""
    
    user = UserSerializer(read_only=True)
    compliance_request = ComplianceRequestSerializer(read_only=True)
    agent = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    # Calculated fields
    is_upcoming = serializers.SerializerMethodField()
    time_until_session = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoCallSession
        fields = [
            'session_id', 'compliance_request', 'user',
            
            # Session Details
            'status', 'status_display', 'purpose', 'scheduled_for',
            'duration_minutes', 'duration_formatted',
            
            # Participants
            'agent', 'agent_name', 'agent_title',
            
            # Video Call Platform
            'platform', 'platform_display', 'meeting_link', 'meeting_id',
            'meeting_password',
            
            # Session Data
            'started_at', 'ended_at', 'actual_duration',
            
            # Recording
            'is_recorded', 'recording_url', 'recording_duration',
            'transcription',
            
            # Verification Outcome
            'verification_passed', 'verification_notes', 'issues_identified',
            'follow_up_required', 'follow_up_notes',
            
            # Security
            'ip_address_user', 'ip_address_agent',
            
            # Notifications
            'user_notified', 'agent_notified', 'reminder_sent',
            
            # Calculated fields
            'is_upcoming', 'time_until_session',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'session_id', 'created_at', 'updated_at',
            'is_upcoming', 'time_until_session', 'duration_formatted'
        ]
    
    def get_is_upcoming(self, obj):
        """Check if session is upcoming"""
        return obj.is_upcoming()
    
    def get_time_until_session(self, obj):
        """Get time until session"""
        delta = obj.time_until_session()
        if delta:
            total_seconds = int(delta.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return None
    
    def get_duration_formatted(self, obj):
        """Format duration"""
        if obj.actual_duration:
            return f"{obj.actual_duration} minutes"
        elif obj.duration_minutes:
            return f"{obj.duration_minutes} minutes (scheduled)"
        return "Not set"


class VideoCallScheduleSerializer(serializers.Serializer):
    """Serializer for scheduling video calls"""
    
    compliance_request_id = serializers.CharField()
    purpose = serializers.CharField(required=False, default='KYC Verification')
    scheduled_for = serializers.DateTimeField()
    duration_minutes = serializers.IntegerField(default=30, min_value=15, max_value=120)
    agent_id = serializers.CharField(required=False)
    platform = serializers.CharField(default='zoom')
    meeting_link = serializers.URLField()
    meeting_id = serializers.CharField(required=False, allow_blank=True)
    meeting_password = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate video call scheduling"""
        # Validate scheduled time is in the future
        if data['scheduled_for'] <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        
        # Validate platform
        allowed_platforms = ['zoom', 'google_meet', 'microsoft_teams', 'custom']
        if data['platform'] not in allowed_platforms:
            raise serializers.ValidationError(
                f"Invalid platform. Allowed: {', '.join(allowed_platforms)}"
            )
        
        return data
    
    def create(self, validated_data):
        """Schedule video call session"""
        from .services import schedule_video_call_session
        
        return schedule_video_call_session(**validated_data)


class ComplianceAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Audit Log model"""
    
    user = UserSerializer(read_only=True)
    compliance_request = ComplianceRequestSerializer(read_only=True)
    kyc_verification = KYCVerificationSerializer(read_only=True)
    entity_type_display = serializers.CharField(source='get_entity_type_display', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    
    # Calculated fields
    time_ago = serializers.SerializerMethodField()
    changes_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceAuditLog
        fields = [
            'log_id',
            
            # Entity Information
            'entity_type', 'entity_type_display', 'entity_id',
            
            # Action Information
            'action_type', 'action_type_display', 'action_description',
            
            # User Information
            'user', 'user_email', 'user_role',
            
            # Changes
            'old_value', 'new_value', 'changed_fields', 'changes_summary',
            
            # Metadata
            'ip_address', 'user_agent', 'location',
            
            # Related Data
            'compliance_request', 'kyc_verification',
            
            # Calculated fields
            'time_ago',
            
            # Timestamps
            'created_at'
        ]
        read_only_fields = ['log_id', 'created_at', 'time_ago', 'changes_summary']
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        delta = timezone.now() - obj.created_at
        
        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def get_changes_summary(self, obj):
        """Generate summary of changes"""
        if obj.changed_fields:
            return f"Changed: {', '.join(obj.changed_fields)}"
        elif obj.old_value and obj.new_value:
            return "Values updated"
        elif obj.new_value and not obj.old_value:
            return "Record created"
        elif obj.old_value and not obj.new_value:
            return "Record deleted"
        return "No changes"


class ComplianceRuleSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Rule model"""
    
    created_by = UserSerializer(read_only=True)
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    applicable_apps_display = serializers.CharField(source='get_applicable_apps_display', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    time_period_display = serializers.CharField(source='get_time_period_display', read_only=True)
    
    # Calculated fields
    is_effective = serializers.SerializerMethodField()
    days_until_effective = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceRule
        fields = [
            'rule_id', 'rule_name', 'rule_description',
            
            # Rule Configuration
            'rule_type', 'rule_type_display', 'applicable_apps',
            'applicable_apps_display', 'priority',
            
            # Conditions
            'condition', 'threshold_amount', 'threshold_currency',
            'time_period', 'time_period_display',
            
            # Actions
            'action', 'action_display', 'action_details',
            
            # Risk Parameters
            'risk_weight', 'risk_multiplier',
            
            # Status
            'is_active', 'is_automated',
            
            # Metadata
            'created_by', 'notes',
            
            # Calculated fields
            'is_effective', 'days_until_effective', 'days_until_expiry',
            
            # Timestamps
            'created_at', 'updated_at', 'effective_from', 'effective_to'
        ]
        read_only_fields = [
            'rule_id', 'created_at', 'updated_at',
            'is_effective', 'days_until_effective', 'days_until_expiry'
        ]
    
    def get_is_effective(self, obj):
        """Check if rule is currently effective"""
        return obj.is_effective()
    
    def get_days_until_effective(self, obj):
        """Get days until rule becomes effective"""
        if obj.effective_from > timezone.now():
            delta = obj.effective_from - timezone.now()
            return delta.days
        return 0
    
    def get_days_until_expiry(self, obj):
        """Get days until rule expires"""
        if obj.effective_to and obj.effective_to > timezone.now():
            delta = obj.effective_to - timezone.now()
            return delta.days
        return None


class ComplianceDashboardStatsSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Dashboard Statistics"""
    
    period_type_display = serializers.CharField(source='get_period_type_display', read_only=True)
    
    # Calculated fields
    total_resolved = serializers.SerializerMethodField()
    resolution_rate = serializers.SerializerMethodField()
    kyc_approval_rate = serializers.SerializerMethodField()
    tac_success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceDashboardStats
        fields = [
            'period_type', 'period_type_display', 'period_start', 'period_end',
            
            # Request Statistics
            'total_requests', 'pending_requests', 'approved_requests',
            'rejected_requests', 'escalated_requests', 'total_resolved',
            'resolution_rate',
            
            # KYC Statistics
            'kyc_submissions', 'kyc_approved', 'kyc_rejected', 'kyc_pending',
            'kyc_approval_rate',
            
            # TAC Statistics
            'tac_generated', 'tac_verified', 'tac_expired', 'tac_failed',
            'tac_success_rate',
            
            # Video Call Statistics
            'video_calls_scheduled', 'video_calls_completed',
            'video_calls_cancelled', 'video_call_success_rate',
            
            # Risk Statistics
            'high_risk_count', 'medium_risk_count', 'low_risk_count',
            'average_risk_score',
            
            # Processing Time
            'avg_processing_time_hours', 'median_processing_time_hours',
            'p90_processing_time_hours',
            
            # App-specific Statistics
            'payments_requests', 'escrow_requests', 'crypto_requests',
            'wallet_requests',
            
            # Compliance Officer Statistics
            'requests_per_officer', 'avg_resolution_time_per_officer',
            
            # Timestamps
            'calculated_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_total_resolved(self, obj):
        """Get total resolved requests"""
        return obj.approved_requests + obj.rejected_requests
    
    def get_resolution_rate(self, obj):
        """Calculate resolution rate"""
        if obj.total_requests > 0:
            return ((obj.approved_requests + obj.rejected_requests) / obj.total_requests) * 100
        return 0
    
    def get_kyc_approval_rate(self, obj):
        """Calculate KYC approval rate"""
        if obj.kyc_submissions > 0:
            return (obj.kyc_approved / obj.kyc_submissions) * 100
        return 0
    
    def get_tac_success_rate(self, obj):
        """Calculate TAC success rate"""
        if obj.tac_generated > 0:
            return (obj.tac_verified / obj.tac_generated) * 100
        return 0


class ComplianceAlertSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Alert model"""
    
    user = UserSerializer(read_only=True)
    compliance_request = ComplianceRequestSerializer(read_only=True)
    kyc_verification = KYCVerificationSerializer(read_only=True)
    acknowledged_by = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    # Calculated fields
    time_since_created = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    requires_action = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceAlert
        fields = [
            'alert_id',
            
            # Alert Details
            'alert_type', 'alert_type_display', 'severity', 'severity_display',
            'title', 'description',
            
            # Related Entities
            'compliance_request', 'kyc_verification', 'user',
            
            # Alert Data
            'alert_data', 'trigger_conditions',
            
            # Status
            'is_resolved', 'is_acknowledged', 'acknowledged_by', 'acknowledged_at',
            
            # Resolution
            'resolution_notes', 'resolved_by', 'resolved_at',
            
            # Notification
            'notified_users', 'notification_sent', 'notification_channels',
            
            # Calculated fields
            'time_since_created', 'is_expired', 'requires_action',
            
            # Timestamps
            'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = [
            'alert_id', 'created_at', 'updated_at',
            'time_since_created', 'is_expired', 'requires_action'
        ]
    
    def get_time_since_created(self, obj):
        """Get time since alert was created"""
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def get_is_expired(self, obj):
        """Check if alert is expired"""
        return obj.is_expired()
    
    def get_requires_action(self, obj):
        """Check if alert requires action"""
        return not obj.is_resolved and not obj.is_acknowledged


class ComplianceAlertCreateSerializer(serializers.Serializer):
    """Serializer for creating compliance alerts"""
    
    alert_type = serializers.CharField()
    severity = serializers.CharField(default='warning')
    title = serializers.CharField()
    description = serializers.CharField()
    compliance_request_id = serializers.CharField(required=False)
    kyc_verification_id = serializers.CharField(required=False)
    user_id = serializers.CharField(required=False)
    alert_data = serializers.JSONField(required=False, default=dict)
    trigger_conditions = serializers.JSONField(required=False, default=dict)
    expires_in_hours = serializers.IntegerField(default=24)
    
    def validate(self, data):
        """Validate alert creation"""
        # Validate alert type
        allowed_types = [
            'risk_threshold', 'suspicious_activity', 'rule_violation',
            'deadline_approaching', 'kyc_expiring', 'document_expiring',
            'unusual_pattern', 'sanctions_match', 'pep_identified'
        ]
        if data['alert_type'] not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid alert type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Validate severity
        allowed_severities = ['info', 'warning', 'error', 'critical']
        if data['severity'] not in allowed_severities:
            raise serializers.ValidationError(
                f"Invalid severity. Allowed: {', '.join(allowed_severities)}"
            )
        
        # Set expires_at
        if data.get('expires_in_hours'):
            data['expires_at'] = timezone.now() + timedelta(hours=data['expires_in_hours'])
        
        return data
    
    def create(self, validated_data):
        """Create compliance alert"""
        from .services import create_compliance_alert
        
        return create_compliance_alert(**validated_data)


class ComplianceDashboardSummarySerializer(serializers.Serializer):
    """Serializer for compliance dashboard summary"""
    
    # Overview
    total_requests_today = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    high_priority_requests = serializers.IntegerField()
    
    # KYC Summary
    kyc_pending_review = serializers.IntegerField()
    kyc_expiring_soon = serializers.IntegerField()
    
    # Alerts
    unresolved_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    
    # Performance
    avg_processing_time = serializers.FloatField()
    resolution_rate = serializers.FloatField()
    
    # Officer Workload
    officer_workload = serializers.DictField()
    
    # Recent Activity
    recent_requests = ComplianceRequestSerializer(many=True)
    recent_alerts = ComplianceAlertSerializer(many=True)


class ComplianceSearchSerializer(serializers.Serializer):
    """Serializer for compliance search results"""
    
    compliance_requests = ComplianceRequestSerializer(many=True)
    kyc_verifications = KYCVerificationSerializer(many=True)
    users = UserSerializer(many=True)
    
    # Counts
    requests_count = serializers.IntegerField()
    kyc_count = serializers.IntegerField()
    users_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class ComplianceBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk compliance actions"""
    
    action = serializers.ChoiceField(choices=['approve', 'reject', 'escalate', 'assign', 'archive'])
    item_ids = serializers.ListField(child=serializers.CharField())
    notes = serializers.CharField(required=False, allow_blank=True)
    assigned_to = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate bulk action"""
        action = data.get('action')
        item_ids = data.get('item_ids', [])
        
        if not item_ids:
            raise serializers.ValidationError("At least one item ID must be provided")
        
        if action == 'assign' and not data.get('assigned_to'):
            raise serializers.ValidationError("assigned_to is required for assign action")
        
        return data
    
    def perform_action(self):
        """Perform bulk action"""
        from .services import perform_bulk_compliance_action
        
        action = self.validated_data['action']
        item_ids = self.validated_data['item_ids']
        notes = self.validated_data.get('notes', '')
        assigned_to = self.validated_data.get('assigned_to')
        
        return perform_bulk_compliance_action(action, item_ids, notes, assigned_to)


class ComplianceExportSerializer(serializers.Serializer):
    """Serializer for compliance data export"""
    
    export_type = serializers.ChoiceField(choices=['requests', 'kyc', 'audit_logs', 'all'])
    format = serializers.ChoiceField(choices=['csv', 'excel', 'json'], default='csv')
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    filters = serializers.JSONField(required=False, default=dict)
    
    def validate(self, data):
        """Validate export parameters"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from cannot be after date_to")
        
        return data


class ComplianceNotificationSerializer(serializers.Serializer):
    """Serializer for compliance notifications"""
    
    notification_type = serializers.CharField()
    recipient_ids = serializers.ListField(child=serializers.CharField(), required=False)
    title = serializers.CharField()
    message = serializers.CharField()
    priority = serializers.CharField(default='normal')
    data = serializers.JSONField(required=False, default=dict)
    
    def validate(self, data):
        """Validate notification parameters"""
        allowed_types = [
            'request_created', 'request_updated', 'request_approved',
            'request_rejected', 'kyc_submitted', 'kyc_approved',
            'kyc_rejected', 'tac_generated', 'video_call_scheduled',
            'alert_created', 'deadline_approaching', 'escalation'
        ]
        
        if data['notification_type'] not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid notification type. Allowed: {', '.join(allowed_types)}"
            )
        
        allowed_priorities = ['low', 'normal', 'high', 'urgent']
        if data['priority'] not in allowed_priorities:
            raise serializers.ValidationError(
                f"Invalid priority. Allowed: {', '.join(allowed_priorities)}"
            )
        
        return data


# Utility serializers
class ComplianceStatsSerializer(serializers.Serializer):
    """Serializer for real-time compliance statistics"""
    
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    today_requests = serializers.IntegerField()
    avg_processing_time = serializers.FloatField()
    approval_rate = serializers.FloatField()
    high_risk_count = serializers.IntegerField()
    
    # Breakdown by app
    by_app = serializers.DictField()
    
    # Breakdown by type
    by_type = serializers.DictField()
    
    # Officer statistics
    officers_busy = serializers.IntegerField()
    officers_available = serializers.IntegerField()


class ComplianceTimelineSerializer(serializers.Serializer):
    """Serializer for compliance request timeline"""
    
    event_type = serializers.CharField()
    event_title = serializers.CharField()
    event_description = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField()
    user = UserSerializer(required=False)
    data = serializers.JSONField(required=False, default=dict)
    
    class Meta:
        fields = ['event_type', 'event_title', 'event_description', 'timestamp', 'user', 'data']


class ComplianceReportSerializer(serializers.Serializer):
    """Serializer for compliance reports"""
    
    report_type = serializers.CharField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    generated_at = serializers.DateTimeField()
    data = serializers.JSONField()
    summary = serializers.DictField()
    download_url = serializers.URLField(required=False)
    
    class Meta:
        fields = ['report_type', 'period_start', 'period_end', 'generated_at', 'data', 'summary', 'download_url']