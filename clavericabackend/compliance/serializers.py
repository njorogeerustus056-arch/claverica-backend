from rest_framework import serializers
from .models import (
    KYCVerification, KYCDocument, ComplianceCheck,
    TACCode, ComplianceAuditLog, WithdrawalRequest,
    DocumentType
)


class KYCSubmissionSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=255)
    first_name = serializers.CharField(max_length=100)
    middle_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100)
    date_of_birth = serializers.DateTimeField()
    nationality = serializers.CharField(max_length=100)
    country_of_residence = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    state_province = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20)
    id_number = serializers.CharField(max_length=100)
    id_type = serializers.ChoiceField(choices=DocumentType.choices)
    occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    source_of_funds = serializers.CharField(max_length=255, required=False, allow_blank=True)
    purpose_of_account = serializers.CharField(max_length=255, required=False, allow_blank=True)


class KYCVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCVerification
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at', 'updated_at']


class DocumentUploadSerializer(serializers.Serializer):
    verification_id = serializers.UUIDField()
    user_id = serializers.CharField(max_length=255)
    document_type = serializers.ChoiceField(choices=DocumentType.choices)
    file = serializers.FileField()


class TACVerificationSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=6)
    transaction_id = serializers.CharField(max_length=255, required=False, allow_blank=True)


class WithdrawalRequestSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=255)
    amount = serializers.FloatField()
    currency = serializers.CharField(max_length=10, default='USD')
    destination_type = serializers.CharField(max_length=50)
    destination_details = serializers.JSONField()


class WithdrawalModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
