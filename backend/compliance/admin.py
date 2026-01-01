"""
compliance/admin.py - Django admin configuration for compliance app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    KYCVerification, KYCDocument, ComplianceCheck,
    TACCode, ComplianceAuditLog, WithdrawalRequest,
    VerificationStatus, DocumentType, ComplianceLevel
)

User = get_user_model()


class UserLinkMixin:
    """
    Mixin to add user links in admin
    """
    
    def user_link(self, obj):
        """
        Create a link to the user admin page
        """
        try:
            user = User.objects.get(id=obj.user_id)
            url = reverse('admin:auth_user_change', args=[user.id])
            return format_html('<a href="{}">{}</a>', url, user.username)
        except (User.DoesNotExist, ValueError):
            return obj.user_id
    
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user_id'


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = [
        'id_short', 'user_link', 'full_name', 'verification_status',
        'compliance_level', 'risk_level', 'created_at', 'verified_at'
    ]
    
    list_filter = [
        'verification_status', 'compliance_level', 'risk_level',
        'nationality', 'country_of_residence', 'created_at'
    ]
    
    search_fields = [
        'user_id', 'first_name', 'last_name', 'email',
        'id_number', 'phone_number'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'risk_score',
        'ip_address', 'user_agent', 'geolocation'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user_id', 'first_name', 'middle_name', 'last_name', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'address_line1', 'address_line2',
                      'city', 'state_province', 'postal_code')
        }),
        ('Identity Information', {
            'fields': ('id_number', 'id_type', 'id_issue_date', 'id_expiry_date',
                      'nationality', 'country_of_residence')
        }),
        ('Verification Status', {
            'fields': ('verification_status', 'compliance_level', 'risk_score',
                      'risk_level', 'verified_by', 'verified_at', 'rejection_reason')
        }),
        ('Additional Information', {
            'fields': ('occupation', 'source_of_funds', 'purpose_of_account',
                      'expected_transaction_volume')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'geolocation', 'notes',
                      'created_at', 'updated_at')
        }),
    )
    
    actions = ['approve_selected', 'reject_selected']
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def full_name(self, obj):
        """Display full name"""
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'
    full_name.admin_order_field = 'first_name'
    
    def approve_selected(self, request, queryset):
        """Approve selected verifications"""
        updated = queryset.update(
            verification_status=VerificationStatus.APPROVED,
            verified_by=str(request.user.id),
            verified_at=timezone.now()
        )
        self.message_user(request, f"{updated} verifications approved.")
    
    approve_selected.short_description = "Approve selected verifications"
    
    def reject_selected(self, request, queryset):
        """Reject selected verifications"""
        # In a real implementation, you would want to collect rejection reason
        updated = queryset.update(
            verification_status=VerificationStatus.REJECTED,
            verified_by=str(request.user.id),
            verified_at=timezone.now(),
            rejection_reason="Rejected via admin action"
        )
        self.message_user(request, f"{updated} verifications rejected.")
    
    reject_selected.short_description = "Reject selected verifications"
    
    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request).select_related(
            # Add any related fields if needed
        )


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = [
        'id_short', 'user_link', 'document_type', 'status',
        'file_size_mb', 'uploaded_at', 'verified_at'
    ]
    
    list_filter = [
        'document_type', 'status', 'uploaded_at', 'verified_at'
    ]
    
    search_fields = [
        'user_id', 'document_number', 'original_file_name',
        'file_name', 'verification__id'
    ]
    
    readonly_fields = [
        'id', 'file_hash', 'file_size', 'file_type',
        'uploaded_at', 'updated_at', 'file_preview'
    ]
    
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'verification', 'user_id', 'document_type', 'document_number')
        }),
        ('File Information', {
            'fields': ('original_file_name', 'file_name', 'file_path',
                      'file_size', 'file_size_mb', 'file_type', 'file_hash',
                      'file_preview')
        }),
        ('Verification Status', {
            'fields': ('status', 'verified_at', 'verified_by',
                      'confidence_score', 'rejection_reason')
        }),
        ('Extracted Data', {
            'fields': ('ocr_data', 'extracted_data', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def file_size_mb(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = 'Size'
    
    def file_preview(self, obj):
        """Display file preview if it's an image"""
        if obj.file_type and obj.file_type.startswith('image/'):
            return format_html(
                '<img src="/media/{}" style="max-width: 300px; max-height: 300px;" />',
                obj.file_path
            )
        return "No preview available"
    file_preview.short_description = 'Preview'


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = [
        'id_short', 'user_link', 'check_type', 'status',
        'risk_score', 'checked_at', 'expires_at'
    ]
    
    list_filter = [
        'check_type', 'status', 'checked_at', 'expires_at'
    ]
    
    search_fields = [
        'user_id', 'provider', 'provider_reference',
        'verification__id'
    ]
    
    readonly_fields = [
        'id', 'checked_at'
    ]
    
    fieldsets = (
        ('Check Information', {
            'fields': ('id', 'verification', 'user_id', 'check_type', 'status')
        }),
        ('Results', {
            'fields': ('result', 'risk_score', 'matches_found')
        }),
        ('Provider Information', {
            'fields': ('provider', 'provider_reference')
        }),
        ('Timestamps', {
            'fields': ('checked_at', 'expires_at', 'notes')
        }),
    )
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'


@admin.register(TACCode)
class TACCodeAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = [
        'id_short', 'user_link', 'code', 'code_type',
        'is_used', 'is_expired', 'created_at', 'expires_at'
    ]
    
    list_filter = [
        'code_type', 'is_used', 'is_expired', 'created_at'
    ]
    
    search_fields = [
        'user_id', 'code', 'transaction_id'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'code'
    ]
    
    fieldsets = (
        ('Code Information', {
            'fields': ('id', 'user_id', 'code', 'code_type')
        }),
        ('Validation Status', {
            'fields': ('is_used', 'is_expired', 'attempts', 'max_attempts',
                      'used_at', 'expires_at')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'amount', 'metadata')
        }),
        ('Security Information', {
            'fields': ('ip_address', 'user_agent', 'created_at')
        }),
    )
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'


@admin.register(ComplianceAuditLog)
class ComplianceAuditLogAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = [
        'id_short', 'user_link', 'action', 'action_type',
        'entity_type', 'created_at', 'ip_address'
    ]
    
    list_filter = [
        'action_type', 'entity_type', 'created_at'
    ]
    
    search_fields = [
        'user_id', 'action', 'entity_id', 'actor_id'
    ]
    
    readonly_fields = [
        'id', 'created_at'
    ]
    
    fieldsets = (
        ('Action Information', {
            'fields': ('id', 'user_id', 'verification_id', 'action', 'action_type',
                      'entity_type', 'entity_id')
        }),
        ('Changes', {
            'fields': ('old_value', 'new_value'),
            'classes': ('collapse',)
        }),
        ('Actor Information', {
            'fields': ('actor_id', 'actor_role')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def has_add_permission(self, request):
        """Prevent adding audit logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent changing audit logs"""
        return False


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin, UserLinkMixin):
    list_display = [
        'id_short', 'user_link', 'amount_formatted', 'currency',
        'status', 'tac_verified', 'created_at', 'processed_at'
    ]
    
    list_filter = [
        'status', 'currency', 'destination_type',
        'tac_verified', 'created_at', 'processed_at'
    ]
    
    search_fields = [
        'user_id', 'transaction_hash', 'processed_by'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'completed_at'
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': ('id', 'user_id', 'amount', 'currency')
        }),
        ('Destination', {
            'fields': ('destination_type', 'destination_details')
        }),
        ('Status', {
            'fields': ('status', 'requires_tac', 'tac_verified', 'tac_code_id')
        }),
        ('Compliance', {
            'fields': ('kyc_status', 'compliance_status')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at', 'transaction_hash')
        }),
        ('Notes', {
            'fields': ('notes', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    actions = ['process_selected', 'cancel_selected']
    
    def id_short(self, obj):
        """Display shortened ID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def amount_formatted(self, obj):
        """Format amount with currency"""
        return f"{obj.currency} {obj.amount:,.2f}"
    amount_formatted.short_description = 'Amount'
    amount_formatted.admin_order_field = 'amount'
    
    def process_selected(self, request, queryset):
        """Process selected withdrawals"""
        updated = queryset.filter(status='pending').update(
            status='processing',
            processed_by=str(request.user.id),
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} withdrawals marked as processing.")
    
    process_selected.short_description = "Process selected withdrawals"
    
    def cancel_selected(self, request, queryset):
        """Cancel selected withdrawals"""
        updated = queryset.filter(status__in=['pending', 'processing']).update(
            status='cancelled',
            processed_by=str(request.user.id),
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} withdrawals cancelled.")
    
    cancel_selected.short_description = "Cancel selected withdrawals"


# Custom admin site configuration
class ComplianceAdminSite(admin.AdminSite):
    """
    Custom admin site for compliance
    """
    site_header = "Compliance Administration"
    site_title = "Compliance Admin"
    index_title = "Compliance Dashboard"


# Register models with custom admin site (optional)
compliance_admin_site = ComplianceAdminSite(name='compliance_admin')

compliance_admin_site.register(KYCVerification, KYCVerificationAdmin)
compliance_admin_site.register(KYCDocument, KYCDocumentAdmin)
compliance_admin_site.register(ComplianceCheck, ComplianceCheckAdmin)
compliance_admin_site.register(TACCode, TACCodeAdmin)
compliance_admin_site.register(ComplianceAuditLog, ComplianceAuditLogAdmin)
compliance_admin_site.register(WithdrawalRequest, WithdrawalRequestAdmin)


# Admin actions for the main admin site
def export_compliance_data(modeladmin, request, queryset):
    """
    Export compliance data as CSV
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="compliance_data.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    if queryset.model == KYCVerification:
        writer.writerow(['ID', 'User ID', 'Name', 'Email', 'Status', 'Risk Level', 'Created At'])
        for obj in queryset:
            writer.writerow([
                str(obj.id)[:8],
                obj.user_id,
                f"{obj.first_name} {obj.last_name}",
                obj.email,
                obj.verification_status,
                obj.risk_level,
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    return response

export_compliance_data.short_description = "Export selected items as CSV"

# Add export action to all compliance models
for model_admin in [KYCVerificationAdmin, WithdrawalRequestAdmin]:
    model_admin.actions.append(export_compliance_data)