"""
kyc/serializers.py - DRF Serializers for KYC API
"""
from rest_framework import serializers
from django.utils import timezone
from .models import KYCDocument, KYCSubmission, KYCSetting


class KYCDocumentSerializer(serializers.ModelSerializer):
    """Serializer for KYC Document upload and status"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_account_number = serializers.CharField(source='user.account_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = KYCDocument
        fields = [
            'id',
            'user_email',
            'user_account_number',
            'document_type',
            'document_type_display',
            'status',
            'status_display',
            'id_front_image',
            'id_back_image',
            'facial_image',
            'admin_notes',
            'rejection_reason',
            'submitted_at',
            'reviewed_at',
            'expires_at',
            'days_until_expiry',
            'is_expired',
            'is_approved'
        ]
        read_only_fields = ['status', 'submitted_at', 'reviewed_at', 'expires_at', 
                          'admin_notes', 'rejection_reason']
    
    def get_days_until_expiry(self, obj):
        if obj.expires_at:
            delta = obj.expires_at - timezone.now()
            return delta.days
        return None
    
    def validate(self, data):
        """Validate document requirements"""
        document_type = data.get('document_type')
        id_back_image = data.get('id_back_image')
        
        # Require back image for certain document types
        if document_type in ['national_id', 'driver_license'] and not id_back_image:
            raise serializers.ValidationError({
                'id_back_image': 'Back image is required for National ID and Driver License'
            })
        
        return data


class KYCStatusSerializer(serializers.Serializer):
    """Serializer for KYC status check"""
    
    has_kyc = serializers.BooleanField()
    is_approved = serializers.BooleanField()
    status = serializers.CharField(required=False)
    status_display = serializers.CharField(required=False)
    submitted_at = serializers.DateTimeField(required=False)
    reviewed_at = serializers.DateTimeField(required=False)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.CharField(required=False)
    
    class Meta:
        fields = ['has_kyc', 'is_approved', 'status', 'status_display', 
                 'submitted_at', 'reviewed_at', 'rejection_reason', 'document_type']


class KYCRequirementSerializer(serializers.Serializer):
    """Serializer for checking KYC requirement"""
    
    service_type = serializers.ChoiceField(choices=KYCSubmission.SERVICE_TYPES)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative")
        return value


class KYCRequirementResponseSerializer(serializers.Serializer):
    """Response serializer for KYC requirement check"""
    
    requires_kyc = serializers.BooleanField()
    has_approved_kyc = serializers.BooleanField()
    threshold_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    requested_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    service_type = serializers.CharField()
    submission_id = serializers.UUIDField(required=False)
    message = serializers.CharField()
    
    class Meta:
        fields = ['requires_kyc', 'has_approved_kyc', 'threshold_amount', 
                 'requested_amount', 'service_type', 'submission_id', 'message']


class KYCSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for KYC submissions"""
    
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    
    class Meta:
        model = KYCSubmission
        fields = [
            'id',
            'service_type',
            'service_type_display',
            'requested_for',
            'amount_triggered',
            'threshold_amount',
            'is_completed',
            'created_at',
            'completed_at'
        ]
        read_only_fields = fields


class KYCSettingSerializer(serializers.ModelSerializer):
    """Serializer for KYC settings"""
    
    service_type_display = serializers.CharField(source='get_service_type_display', read_only=True)
    
    class Meta:
        model = KYCSetting
        fields = [
            'id',
            'service_type',
            'service_type_display',
            'requires_kyc',
            'threshold_amount',
            'is_active',
            'updated_at'
        ]