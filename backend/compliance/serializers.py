"""
compliance/serializers.py - Django REST Framework serializers for compliance app
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime
import uuid

from .models import (
    KYCVerification, KYCDocument, ComplianceCheck,
    TACCode, ComplianceAuditLog, WithdrawalRequest,
    VerificationStatus, DocumentType, ComplianceLevel
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class KYCSubmissionSerializer(serializers.Serializer):
    """Serializer for KYC submission"""
    
    # Personal Information
    first_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateTimeField()
    nationality = serializers.CharField(max_length=100)
    country_of_residence = serializers.CharField(max_length=100)
    
    # Contact Information
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state_province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20)
    
    # Identity Information
    id_number = serializers.CharField(max_length=100)
    id_type = serializers.ChoiceField(choices=DocumentType.choices)
    id_issue_date = serializers.DateTimeField(required=False, allow_null=True)
    id_expiry_date = serializers.DateTimeField(required=False, allow_null=True)
    
    # Additional Information
    occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    source_of_funds = serializers.CharField(max_length=255, required=False, allow_blank=True)
    purpose_of_account = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expected_transaction_volume = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate KYC submission data"""
        # Validate date of birth (must be at least 18 years old)
        date_of_birth = data.get('date_of_birth')
        if date_of_birth:
            age = (timezone.now().date() - date_of_birth.date()).days // 365
            if age < 18:
                raise serializers.ValidationError("You must be at least 18 years old")
        
        # Validate ID expiry date if provided
        id_expiry_date = data.get('id_expiry_date')
        if id_expiry_date and id_expiry_date < timezone.now():
            raise serializers.ValidationError("ID document has expired")
        
        return data


class KYCVerificationSerializer(serializers.ModelSerializer):
    """Serializer for KYC Verification model"""
    
    user = UserSerializer(read_only=True, source='get_user')
    id_type_display = serializers.CharField(source='get_id_type_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    compliance_level_display = serializers.CharField(source='get_compliance_level_display', read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCVerification
        fields = [
            'id', 'user_id', 'user', 'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'nationality', 'country_of_residence',
            'email', 'phone_number', 'address_line1', 'address_line2',
            'city', 'state_province', 'postal_code', 'id_number',
            'id_type', 'id_type_display', 'id_issue_date', 'id_expiry_date',
            'compliance_level', 'compliance_level_display',
            'verification_status', 'verification_status_display',
            'risk_score', 'risk_level', 'verified_by', 'verified_at',
            'rejection_reason', 'notes', 'occupation', 'source_of_funds',
            'purpose_of_account', 'expected_transaction_volume',
            'ip_address', 'user_agent', 'geolocation',
            'documents_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'verified_at',
            'risk_score', 'risk_level', 'ip_address', 'user_agent'
        ]
    
    def get_documents_count(self, obj):
        """Get count of documents for this verification"""
        return obj.documents.count()
    
    def get_user(self, obj):
        """Get user object if user_id corresponds to a User model"""
        try:
            return User.objects.get(id=obj.user_id)
        except (User.DoesNotExist, ValueError):
            return None


class KYCVerificationDetailSerializer(KYCVerificationSerializer):
    """Detailed serializer for KYC Verification with documents"""
    
    documents = serializers.SerializerMethodField()
    
    class Meta(KYCVerificationSerializer.Meta):
        fields = KYCVerificationSerializer.Meta.fields + ['documents']
    
    def get_documents(self, obj):
        """Get all documents for this verification"""
        documents = obj.documents.all()
        return KYCDocumentSerializer(documents, many=True).data


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC Document model"""
    
    verification = KYCVerificationSerializer(read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCDocument
        fields = [
            'id', 'verification', 'user_id', 'document_type',
            'document_type_display', 'document_number',
            'file_name', 'original_file_name', 'file_path', 'file_url',
            'file_size', 'file_size_mb', 'file_type', 'file_hash',
            'status', 'status_display', 'verified_at', 'verified_by',
            'ocr_data', 'extracted_data', 'confidence_score',
            'notes', 'rejection_reason', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_name', 'file_path', 'file_hash',
            'file_size', 'file_type', 'uploaded_at', 'updated_at'
        ]
    
    def get_file_url(self, obj):
        """Generate file URL for download"""
        request = self.context.get('request')
        if request and obj.file_path:
            return request.build_absolute_uri(f'/media/{obj.file_path}')
        return None
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""
    
    verification_id = serializers.UUIDField()
    document_type = serializers.ChoiceField(choices=DocumentType.choices)
    file = serializers.FileField()
    document_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_verification_id(self, value):
        """Validate verification exists"""
        try:
            verification = KYCVerification.objects.get(id=value)
            # Check if verification belongs to current user
            request = self.context.get('request')
            if request and str(verification.user_id) != str(request.user.id):
                raise serializers.ValidationError("Verification does not belong to user")
            return value
        except KYCVerification.DoesNotExist:
            raise serializers.ValidationError("Verification not found")


class ComplianceCheckSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Check model"""
    
    verification = KYCVerificationSerializer(read_only=True)
    
    class Meta:
        model = ComplianceCheck
        fields = [
            'id', 'verification', 'user_id', 'check_type', 'status',
            'result', 'risk_score', 'matches_found', 'provider',
            'provider_reference', 'checked_at', 'expires_at', 'notes'
        ]
        read_only_fields = ['id', 'checked_at']


class TACCodeSerializer(serializers.ModelSerializer):
    """Serializer for TAC Code model"""
    
    is_valid = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = TACCode
        fields = [
            'id', 'user_id', 'code', 'code_type', 'is_used',
            'is_expired', 'attempts', 'max_attempts', 'transaction_id',
            'amount', 'metadata', 'is_valid', 'time_remaining',
            'created_at', 'expires_at', 'used_at', 'ip_address',
            'user_agent'
        ]
        read_only_fields = [
            'id', 'code', 'created_at', 'expires_at',
            'is_used', 'is_expired', 'attempts'
        ]
        extra_kwargs = {
            'code': {'write_only': True}  # Hide code in responses
        }
    
    def get_is_valid(self, obj):
        """Check if TAC code is still valid"""
        if obj.is_used or obj.is_expired:
            return False
        return obj.expires_at > timezone.now()
    
    def get_time_remaining(self, obj):
        """Get time remaining in seconds"""
        if obj.is_used or obj.is_expired or obj.expires_at <= timezone.now():
            return 0
        return (obj.expires_at - timezone.now()).total_seconds()


class TACVerificationSerializer(serializers.Serializer):
    """Serializer for TAC verification"""
    
    code = serializers.CharField(max_length=6)
    transaction_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_code(self, value):
        """Validate TAC code format"""
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("TAC code must be 6 digits")
        return value


class TACGenerationSerializer(serializers.Serializer):
    """Serializer for TAC generation"""
    
    transaction_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    amount = serializers.FloatField(required=False, allow_null=True)
    code_type = serializers.CharField(max_length=20, default='withdrawal')


class ComplianceAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for Compliance Audit Log"""
    
    actor = UserSerializer(read_only=True, source='get_actor')
    
    class Meta:
        model = ComplianceAuditLog
        fields = [
            'id', 'user_id', 'verification_id', 'action', 'action_type',
            'entity_type', 'entity_id', 'old_value', 'new_value',
            'actor_id', 'actor', 'actor_role', 'ip_address', 'user_agent',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_actor(self, obj):
        """Get actor user object if actor_id corresponds to a User model"""
        if obj.actor_id:
            try:
                return User.objects.get(id=obj.actor_id)
            except (User.DoesNotExist, ValueError):
                return None
        return None


class WithdrawalRequestSerializer(serializers.Serializer):
    """Serializer for withdrawal request creation"""
    
    amount = serializers.FloatField(min_value=0.01)
    currency = serializers.CharField(max_length=10, default='USD')
    destination_type = serializers.CharField(max_length=50)
    destination_details = serializers.JSONField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        """Validate withdrawal amount"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_destination_details(self, value):
        """Validate destination details based on type"""
        destination_type = self.initial_data.get('destination_type', '')
        
        if destination_type == 'bank_account':
            required_fields = ['account_number', 'account_name', 'bank_name', 'bank_code']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(f"{field} is required for bank transfers")
        
        elif destination_type == 'crypto_wallet':
            required_fields = ['wallet_address', 'network']
            for field in required_fields:
                if field not in value:
                    raise serializers.ValidationError(f"{field} is required for crypto transfers")
        
        return value


class WithdrawalModelSerializer(serializers.ModelSerializer):
    """Serializer for Withdrawal Request model"""
    
    user = UserSerializer(read_only=True, source='get_user')
    destination_details_formatted = serializers.SerializerMethodField()
    processing_time = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user_id', 'user', 'amount', 'currency',
            'destination_type', 'destination_details', 'destination_details_formatted',
            'status', 'requires_tac', 'tac_verified', 'tac_code_id',
            'kyc_status', 'compliance_status', 'processed_by', 'processed_at',
            'transaction_hash', 'notes', 'rejection_reason',
            'processing_time', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'tac_verified', 'tac_code_id',
            'processed_by', 'processed_at', 'transaction_hash',
            'created_at', 'updated_at', 'completed_at'
        ]
    
    def get_destination_details_formatted(self, obj):
        """Format destination details for display"""
        details = obj.destination_details or {}
        
        if obj.destination_type == 'bank_account':
            return {
                'account_number': details.get('account_number', ''),
                'account_name': details.get('account_name', ''),
                'bank_name': details.get('bank_name', ''),
                'masked_account': f"****{details.get('account_number', '')[-4:]}" if details.get('account_number') else ''
            }
        
        elif obj.destination_type == 'crypto_wallet':
            return {
                'wallet_address': details.get('wallet_address', ''),
                'network': details.get('network', ''),
                'masked_address': f"{details.get('wallet_address', '')[:8]}...{details.get('wallet_address', '')[-4:]}" if details.get('wallet_address') else ''
            }
        
        return details
    
    def get_processing_time(self, obj):
        """Calculate processing time"""
        if obj.completed_at and obj.created_at:
            return (obj.completed_at - obj.created_at).total_seconds()
        elif obj.processed_at and obj.created_at:
            return (obj.processed_at - obj.created_at).total_seconds()
        return None
    
    def get_user(self, obj):
        """Get user object if user_id corresponds to a User model"""
        try:
            return User.objects.get(id=obj.user_id)
        except (User.DoesNotExist, ValueError):
            return None


class KYCStatisticsSerializer(serializers.Serializer):
    """Serializer for KYC statistics"""
    
    total_verifications = serializers.IntegerField()
    pending_verifications = serializers.IntegerField()
    approved_verifications = serializers.IntegerField()
    rejected_verifications = serializers.IntegerField()
    average_processing_time = serializers.FloatField()
    high_risk_count = serializers.IntegerField()


class ComplianceDashboardSerializer(serializers.Serializer):
    """Serializer for compliance dashboard"""
    
    kyc_statistics = KYCStatisticsSerializer()
    recent_withdrawals = WithdrawalModelSerializer(many=True)
    pending_actions = serializers.IntegerField()
    audit_log_summary = serializers.DictField()


class UserComplianceStatusSerializer(serializers.Serializer):
    """Serializer for user compliance status"""
    
    user_id = serializers.CharField()
    kyc = serializers.DictField()
    withdrawals = serializers.DictField()
    audit_logs = serializers.DictField()
    compliance_score = serializers.FloatField()
    restrictions = serializers.ListField(child=serializers.CharField())


class DocumentVerificationSerializer(serializers.Serializer):
    """Serializer for document verification"""
    
    document_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=VerificationStatus.choices)
    verified_by = serializers.CharField(max_length=255, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate document verification"""
        status = data.get('status')
        rejection_reason = data.get('rejection_reason')
        
        if status == VerificationStatus.REJECTED and not rejection_reason:
            raise serializers.ValidationError({
                "rejection_reason": "Rejection reason is required when rejecting a document"
            })
        
        return data


class BulkDocumentUploadSerializer(serializers.Serializer):
    """Serializer for bulk document upload"""
    
    verification_id = serializers.UUIDField()
    documents = serializers.ListField(
        child=serializers.DictField(child=serializers.FileField()),
        min_length=1,
        max_length=10
    )
    
    def validate_documents(self, value):
        """Validate documents list"""
        for doc in value:
            if 'file' not in doc or 'document_type' not in doc:
                raise serializers.ValidationError("Each document must have 'file' and 'document_type'")
        
        return value


class RiskAssessmentSerializer(serializers.Serializer):
    """Serializer for risk assessment"""
    
    risk_score = serializers.FloatField(min_value=0, max_value=100)
    risk_level = serializers.CharField(max_length=20)
    factors = serializers.ListField(child=serializers.DictField())
    recommendations = serializers.ListField(child=serializers.CharField())


class ComplianceSettingsSerializer(serializers.Serializer):
    """Serializer for compliance settings"""
    
    kyc_auto_approval = serializers.BooleanField(default=False)
    tac_expiry_minutes = serializers.IntegerField(min_value=1, max_value=60, default=5)
    tac_max_attempts = serializers.IntegerField(min_value=1, max_value=10, default=3)
    withdrawal_limit_daily = serializers.FloatField(min_value=0, default=10000)
    withdrawal_limit_monthly = serializers.FloatField(min_value=0, default=50000)
    require_tac_above = serializers.FloatField(min_value=0, default=1000)
    high_risk_countries = serializers.ListField(child=serializers.CharField(), default=list)
    restricted_occupations = serializers.ListField(child=serializers.CharField(), default=list)