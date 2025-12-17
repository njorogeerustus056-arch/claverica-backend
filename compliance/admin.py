from django.contrib import admin
from .models import (
    KYCVerification, KYCDocument, ComplianceCheck,
    TACCode, ComplianceAuditLog, WithdrawalRequest
)


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'first_name', 'last_name', 'verification_status', 'compliance_level', 'created_at']
    list_filter = ['verification_status', 'compliance_level', 'risk_level', 'created_at']
    search_fields = ['user_id', 'first_name', 'last_name', 'email', 'id_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user_id', 'first_name', 'middle_name', 'last_name', 'date_of_birth')
        }),
        ('Contact', {
            'fields': ('email', 'phone_number', 'address_line1', 'address_line2', 'city', 'state_province', 'postal_code')
        }),
        ('Identity', {
            'fields': ('id_number', 'id_type', 'id_issue_date', 'id_expiry_date', 'nationality', 'country_of_residence')
        }),
        ('Verification', {
            'fields': ('verification_status', 'compliance_level', 'risk_score', 'risk_level', 'verified_by', 'verified_at', 'rejection_reason')
        }),
        ('Additional Info', {
            'fields': ('occupation', 'source_of_funds', 'purpose_of_account', 'expected_transaction_volume')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'geolocation', 'notes', 'created_at', 'updated_at')
        }),
    )


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'document_type', 'status', 'uploaded_at', 'verified_at']
    list_filter = ['document_type', 'status', 'uploaded_at']
    search_fields = ['user_id', 'document_number', 'original_file_name']
    readonly_fields = ['id', 'uploaded_at', 'updated_at', 'file_hash']


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'check_type', 'status', 'risk_score', 'checked_at']
    list_filter = ['check_type', 'status', 'checked_at']
    search_fields = ['user_id', 'provider', 'provider_reference']
    readonly_fields = ['id', 'checked_at']


@admin.register(TACCode)
class TACCodeAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'code', 'code_type', 'is_used', 'is_expired', 'created_at', 'expires_at']
    list_filter = ['code_type', 'is_used', 'is_expired', 'created_at']
    search_fields = ['user_id', 'code', 'transaction_id']
    readonly_fields = ['id', 'created_at']


@admin.register(ComplianceAuditLog)
class ComplianceAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'action', 'action_type', 'entity_type', 'created_at']
    list_filter = ['action_type', 'entity_type', 'created_at']
    search_fields = ['user_id', 'action', 'entity_id']
    readonly_fields = ['id', 'created_at']


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'amount', 'currency', 'status', 'tac_verified', 'created_at']
    list_filter = ['status', 'currency', 'destination_type', 'tac_verified', 'created_at']
    search_fields = ['user_id', 'transaction_hash']
    readonly_fields = ['id', 'created_at', 'updated_at']
