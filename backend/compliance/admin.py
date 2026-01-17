"""
compliance/admin.py - Django admin configuration for central compliance app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Avg, Q

from .models import (
    ComplianceRequest, KYCVerification, KYCDocument,
    TACRequest, VideoCallSession, ComplianceAuditLog,
    ComplianceRule, ComplianceDashboardStats, ComplianceAlert
)

def get_user_model_lazy():
    """Lazy function to get user model"""
    from django.contrib.auth import get_user_model
    return get_user_model()



class ComplianceRequestAdmin(admin.ModelAdmin):
    """Admin for Compliance Requests"""
    
    list_display = [
        'compliance_id_short', 'user_link', 'app_name_display',
        'request_type_display', 'amount_display', 'status_display',
        'risk_level_badge', 'priority_display', 'created_at', 'resolved_at'
    ]
    
    list_filter = [
        'app_name', 'request_type', 'status', 'risk_level',
        'priority', 'requires_manual_review', 'requires_tac',
        'requires_video_call', 'created_at'
    ]
    
    search_fields = [
        'compliance_id', 'user__email', 'user__first_name',
        'user__last_name', 'description', 'app_transaction_id'
    ]
    
    readonly_fields = [
        'compliance_id', 'created_at', 'updated_at', 'resolved_at',
        'risk_score', 'ip_address', 'user_agent', 'user_link',
        'tac_code', 'tac_generated_at', 'tac_verified_at',
        'video_call_scheduled_at', 'video_call_completed_at',
        'reviewed_by_link', 'reviewed_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('compliance_id', 'app_name', 'app_transaction_id', 'user_link')
        }),
        ('Request Details', {
            'fields': ('request_type', 'amount', 'currency', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'requires_kyc', 'requires_video_call',
                      'requires_tac', 'requires_manual_review')
        }),
        ('Risk Assessment', {
            'fields': ('risk_score', 'risk_level', 'kyc_verification')
        }),
        ('Workflow', {
            'fields': ('assigned_to', 'reviewed_by_link', 'reviewed_at',
                      'review_notes', 'decision', 'decision_reason')
        }),
        ('Verification', {
            'fields': ('tac_code', 'tac_generated_at', 'tac_verified_at',
                      'video_call_scheduled_at', 'video_call_link',
                      'video_call_completed_at', 'video_call_duration',
                      'video_call_notes')
        }),
        ('Data', {
            'fields': ('form_data', 'documents', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at', 'expires_at')
        }),
        ('Technical', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    actions = ['approve_selected', 'reject_selected', 'assign_to_me']
    
    def compliance_id_short(self, obj):
        return obj.compliance_id[:12]
    compliance_id_short.short_description = 'ID'
    compliance_id_short.admin_order_field = 'compliance_id'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return obj.user_email
    user_link.short_description = 'User'
    
    def reviewed_by_link(self, obj):
        if obj.reviewed_by:
            url = reverse('admin:auth_user_change', args=[obj.reviewed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.email)
        return None
    reviewed_by_link.short_description = 'Reviewed By'
    
    def app_name_display(self, obj):
        return obj.get_app_name_display()
    app_name_display.short_description = 'App'
    
    def request_type_display(self, obj):
        return obj.get_request_type_display()
    request_type_display.short_description = 'Type'
    
    def amount_display(self, obj):
        if obj.amount:
            return f"{obj.currency} {obj.amount:,.2f}"
        return '-'
    amount_display.short_description = 'Amount'
    
    def status_display(self, obj):
        status_colors = {
            'pending': 'orange',
            'under_review': 'blue',
            'approved': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def risk_level_badge(self, obj):
        risk_colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'very_high': 'darkred',
        }
        color = risk_colors.get(obj.risk_level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_risk_level_display().upper()
        )
    risk_level_badge.short_description = 'Risk'
    
    def priority_display(self, obj):
        priority_colors = {
            'low': 'gray',
            'normal': 'blue',
            'high': 'orange',
            'urgent': 'red',
        }
        color = priority_colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'
    
    def approve_selected(self, request, queryset):
        """Approve selected compliance requests"""
        from .services import ComplianceService
        
        count = 0
        for req in queryset.filter(status__in=['pending', 'under_review']):
            result = ComplianceService.approve_request(req, request.user, 'Approved via admin')
            if result['success']:
                count += 1
        
        self.message_user(request, f"{count} requests approved.")
    
    approve_selected.short_description = "Approve selected requests"
    
    def reject_selected(self, request, queryset):
        """Reject selected compliance requests"""
        from .services import ComplianceService
        
        count = 0
        for req in queryset.filter(status__in=['pending', 'under_review']):
            result = ComplianceService.reject_request(req, request.user, 'Rejected via admin', 'Rejected via admin action')
            if result['success']:
                count += 1
        
        self.message_user(request, f"{count} requests rejected.")
    
    reject_selected.short_description = "Reject selected requests"
    
    def assign_to_me(self, request, queryset):
        """Assign selected requests to current admin"""
        count = queryset.update(assigned_to=request.user)
        self.message_user(request, f"{count} requests assigned to you.")
    
    assign_to_me.short_description = "Assign to me"
    
    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request).select_related(
            'user', 'reviewed_by', 'assigned_to', 'kyc_verification'
        ).prefetch_related('video_calls')
    
    def changelist_view(self, request, extra_context=None):
        """Add stats to changelist view"""
        extra_context = extra_context or {}
        
        # Get statistics
        stats = {
            'total': ComplianceRequest.objects.count(),
            'pending': ComplianceRequest.objects.filter(status='pending').count(),
            'under_review': ComplianceRequest.objects.filter(status='under_review').count(),
            'approved': ComplianceRequest.objects.filter(status='approved').count(),
            'rejected': ComplianceRequest.objects.filter(status='rejected').count(),
            'high_risk': ComplianceRequest.objects.filter(risk_level='high').count(),
            'urgent': ComplianceRequest.objects.filter(priority='urgent').count(),
        }
        
        extra_context['stats'] = stats
        return super().changelist_view(request, extra_context=extra_context)


class KYCVerificationAdmin(admin.ModelAdmin):
    """Admin for KYC Verifications"""
    
    list_display = [
        'kyc_id_short', 'user_link', 'full_name', 'verification_status_badge',
        'compliance_level_badge', 'risk_level_badge', 'documents_count',
        'created_at', 'verified_at'
    ]
    
    list_filter = [
        'verification_status', 'compliance_level', 'risk_level',
        'nationality', 'country_of_residence', 'pep_status',
        'sanctions_match', 'created_at', 'verified_at'
    ]
    
    search_fields = [
        'kyc_id', 'user__email', 'first_name', 'last_name',
        'id_number', 'email', 'phone_number'
    ]
    
    readonly_fields = [
        'kyc_id', 'age', 'full_name', 'created_at', 'updated_at',
        'risk_score', 'risk_factors', 'pep_status', 'sanctions_match',
        'sanctions_details', 'submitted_at', 'verified_by_link',
        'documents_submitted', 'documents_approved', 'documents_rejected',
        'pep_check_completed', 'sanctions_check_completed',
        'adverse_media_check_completed', 'document_verification_completed',
        'ip_address', 'user_agent'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('kyc_id', 'user_link', 'full_name', 'age')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'date_of_birth',
                      'nationality', 'country_of_residence', 'country_of_birth')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'address_line1', 'address_line2',
                      'city', 'state_province', 'postal_code')
        }),
        ('Identity Information', {
            'fields': ('id_number', 'id_type', 'id_issue_date', 'id_expiry_date',
                      'id_issuing_country')
        }),
        ('Business Information', {
            'fields': ('company_name', 'company_registration_number',
                      'business_nature', 'website'),
            'classes': ('collapse',)
        }),
        ('Employment Information', {
            'fields': ('occupation', 'employer_name', 'employment_status'),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': ('annual_income', 'income_currency', 'source_of_funds',
                      'expected_monthly_volume', 'purpose_of_account'),
            'classes': ('collapse',)
        }),
        ('Verification Status', {
            'fields': ('verification_status', 'compliance_level', 'verified_by_link',
                      'verified_at', 'review_notes', 'rejection_reason')
        }),
        ('Risk Assessment', {
            'fields': ('risk_score', 'risk_level', 'risk_factors', 'pep_status',
                      'pep_details', 'sanctions_match', 'sanctions_details')
        }),
        ('Compliance Checks', {
            'fields': ('pep_check_completed', 'sanctions_check_completed',
                      'adverse_media_check_completed', 'document_verification_completed'),
            'classes': ('collapse',)
        }),
        ('Document Information', {
            'fields': ('documents_submitted', 'documents_approved', 'documents_rejected'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at', 'next_review_date')
        }),
        ('Technical', {
            'fields': ('ip_address', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    actions = ['approve_selected', 'reject_selected']
    
    def kyc_id_short(self, obj):
        return obj.kyc_id[:12]
    kyc_id_short.short_description = 'KYC ID'
    kyc_id_short.admin_order_field = 'kyc_id'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def verified_by_link(self, obj):
        if obj.verified_by:
            url = reverse('admin:auth_user_change', args=[obj.verified_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.verified_by.email)
        return '-'
    verified_by_link.short_description = 'Verified By'
    
    def full_name(self, obj):
        return obj.full_name()
    full_name.short_description = 'Full Name'
    
    def age(self, obj):
        return obj.age()
    age.short_description = 'Age'
    
    def verification_status_badge(self, obj):
        status_colors = {
            'pending': 'orange',
            'in_review': 'blue',
            'approved': 'green',
            'rejected': 'red',
            'expired': 'gray',
        }
        color = status_colors.get(obj.verification_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_verification_status_display()
        )
    verification_status_badge.short_description = 'Status'
    
    def compliance_level_badge(self, obj):
        level_colors = {
            'basic': 'gray',
            'standard': 'blue',
            'enhanced': 'green',
            'premium': 'gold',
        }
        color = level_colors.get(obj.compliance_level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_compliance_level_display()
        )
    compliance_level_badge.short_description = 'Level'
    
    def risk_level_badge(self, obj):
        risk_colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'very_high': 'darkred',
        }
        color = risk_colors.get(obj.risk_level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.risk_level.upper()
        )
    risk_level_badge.short_description = 'Risk'
    
    def documents_count(self, obj):
        total = obj.documents.count()
        approved = obj.documents.filter(status='approved').count()
        
        if approved == total and total > 0:
            color = 'green'
            text = f'{approved}/{total}'
        elif approved > 0:
            color = 'orange'
            text = f'{approved}/{total}'
        else:
            color = 'red'
            text = f'0/{total}'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    documents_count.short_description = 'Documents'
    
    def approve_selected(self, request, queryset):
        """Approve selected KYC verifications"""
        from .services import KYCService
        
        count = 0
        for kyc in queryset.filter(verification_status__in=['pending', 'in_review']):
            result = KYCService.approve_verification(kyc, request.user, 'Approved via admin')
            if result['success']:
                count += 1
        
        self.message_user(request, f"{count} KYC verifications approved.")
    
    approve_selected.short_description = "Approve selected KYC"
    
    def reject_selected(self, request, queryset):
        """Reject selected KYC verifications"""
        from .services import KYCService
        
        count = 0
        for kyc in queryset.filter(verification_status__in=['pending', 'in_review']):
            result = KYCService.reject_verification(kyc, request.user, 'Rejected via admin')
            if result['success']:
                count += 1
        
        self.message_user(request, f"{count} KYC verifications rejected.")
    
    reject_selected.short_description = "Reject selected KYC"
    
    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request).select_related(
            'user', 'verified_by'
        ).prefetch_related('documents')


class KYCDocumentAdmin(admin.ModelAdmin):
    """Admin for KYC Documents"""
    
    list_display = [
        'document_id_short', 'user_link', 'kyc_link', 'document_type_display',
        'status_badge', 'file_size_display', 'verified_at', 'uploaded_at'
    ]
    
    list_filter = [
        'document_type', 'status', 'is_encrypted', 'uploaded_at', 'verified_at'
    ]
    
    search_fields = [
        'document_id', 'document_number', 'original_file_name',
        'user__email', 'kyc_verification__kyc_id'
    ]
    
    readonly_fields = [
        'document_id', 'file_hash', 'file_size', 'file_type',
        'uploaded_at', 'updated_at', 'file_preview', 'user_link',
        'kyc_link', 'verified_by_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('document_id', 'kyc_link', 'user_link', 'document_type', 'document_number')
        }),
        ('Document Details', {
            'fields': ('document_name', 'issue_date', 'expiry_date',
                      'issuing_country', 'issuing_authority')
        }),
        ('File Information', {
            'fields': ('original_file_name', 'file_name', 'file_path', 'file_url',
                      'file_size_display', 'file_type', 'file_hash', 'file_preview')
        }),
        ('Verification Status', {
            'fields': ('status', 'verified_by_link', 'verified_at',
                      'verification_method', 'confidence_score',
                      'rejection_reason')
        }),
        ('Extracted Data', {
            'fields': ('ocr_data', 'extracted_data', 'notes'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('is_encrypted', 'encryption_key'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at')
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'uploaded_at'
    actions = ['approve_selected', 'reject_selected']
    
    def document_id_short(self, obj):
        return obj.document_id[:12]
    document_id_short.short_description = 'ID'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def kyc_link(self, obj):
        if obj.kyc_verification:
            url = reverse('admin:compliance_kycverification_change', args=[obj.kyc_verification.id])
            return format_html('<a href="{}">{}</a>', url, obj.kyc_verification.kyc_id[:12])
        return '-'
    kyc_link.short_description = 'KYC'
    
    def verified_by_link(self, obj):
        if obj.verified_by:
            url = reverse('admin:auth_user_change', args=[obj.verified_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.verified_by.email)
        return '-'
    verified_by_link.short_description = 'Verified By'
    
    def document_type_display(self, obj):
        return obj.get_document_type_display()
    document_type_display.short_description = 'Type'
    
    def status_badge(self, obj):
        status_colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'expired': 'gray',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def file_size_display(self, obj):
        return f"{obj.file_size_mb():.2f} MB"
    file_size_display.short_description = 'Size'
    
    def file_preview(self, obj):
        """Display file preview if it's an image"""
        if obj.file_type and obj.file_type.startswith('image/'):
            return format_html(
                '<img src="/media/{}" style="max-width: 300px; max-height: 300px;" />',
                obj.file_path
            )
        return format_html('<p>No preview available for {}</p>', obj.file_type)
    file_preview.short_description = 'Preview'
    
    def approve_selected(self, request, queryset):
        """Approve selected documents"""
        from .services import KYCService
        
        count = 0
        for doc in queryset.filter(status='pending'):
            result = KYCService.verify_document(doc, request.user, 'approved', 'Approved via admin')
            if result['success']:
                count += 1
        
        self.message_user(request, f"{count} documents approved.")
    
    approve_selected.short_description = "Approve selected documents"
    
    def reject_selected(self, request, queryset):
        """Reject selected documents"""
        from .services import KYCService
        
        count = 0
        for doc in queryset.filter(status='pending'):
            result = KYCService.verify_document(doc, request.user, 'rejected', 'Rejected via admin', 'Rejected via admin action')
            if result['success']:
                count += 1
        
        self.message_user(request, f"{count} documents rejected.")
    
    reject_selected.short_description = "Reject selected documents"


class TACRequestAdmin(admin.ModelAdmin):
    """Admin for TAC Requests"""
    
    list_display = [
        'tac_id_short', 'user_link', 'tac_type_display', 'is_valid_badge',
        'sent_via_display', 'delivery_status_badge', 'created_at', 'expires_at'
    ]
    
    list_filter = [
        'tac_type', 'is_used', 'is_expired', 'sent_via', 'delivery_status',
        'created_at', 'expires_at'
    ]
    
    search_fields = [
        'tac_id', 'tac_code', 'user__email', 'transaction_id'
    ]
    
    readonly_fields = [
        'tac_id', 'tac_code', 'is_valid', 'time_remaining',
        'created_at', 'expires_at', 'used_at', 'user_link',
        'compliance_request_link', 'verified_by_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tac_id', 'user_link', 'compliance_request_link', 'tac_type', 'purpose')
        }),
        ('TAC Details', {
            'fields': ('tac_code', 'is_used', 'is_expired', 'attempts', 'max_attempts')
        }),
        ('Transaction Details', {
            'fields': ('amount', 'currency', 'transaction_id', 'metadata')
        }),
        ('Delivery', {
            'fields': ('sent_via', 'sent_to', 'delivery_status', 'delivery_attempts')
        }),
        ('Verification', {
            'fields': ('verified_by_link', 'verified_at', 'verification_ip',
                      'verification_user_agent')
        }),
        ('Status', {
            'fields': ('is_valid', 'time_remaining')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'used_at')
        }),
        ('Technical', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def tac_id_short(self, obj):
        return obj.tac_id[:12]
    tac_id_short.short_description = 'ID'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def compliance_request_link(self, obj):
        if obj.compliance_request:
            url = reverse('admin:compliance_compliancerequest_change', args=[obj.compliance_request.id])
            return format_html('<a href="{}">{}</a>', url, obj.compliance_request.compliance_id[:12])
        return '-'
    compliance_request_link.short_description = 'Compliance Request'
    
    def verified_by_link(self, obj):
        if obj.verified_by:
            url = reverse('admin:auth_user_change', args=[obj.verified_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.verified_by.email)
        return '-'
    verified_by_link.short_description = 'Verified By'
    
    def tac_type_display(self, obj):
        return obj.get_tac_type_display()
    tac_type_display.short_description = 'Type'
    
    def sent_via_display(self, obj):
        return obj.get_sent_via_display()
    sent_via_display.short_description = 'Sent Via'
    
    def is_valid_badge(self, obj):
        if obj.is_valid():
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">VALID</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">INVALID</span>'
            )
    is_valid_badge.short_description = 'Valid'
    
    def delivery_status_badge(self, obj):
        status_colors = {
            'pending': 'orange',
            'sent': 'blue',
            'delivered': 'green',
            'failed': 'red',
            'read': 'purple',
        }
        color = status_colors.get(obj.delivery_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_delivery_status_display()
        )
    delivery_status_badge.short_description = 'Delivery'


class VideoCallSessionAdmin(admin.ModelAdmin):
    """Admin for Video Call Sessions"""
    
    list_display = [
        'session_id_short', 'user_link', 'compliance_request_link',
        'status_badge', 'scheduled_for', 'agent_link', 'platform_display',
        'verification_passed_badge'
    ]
    
    list_filter = [
        'status', 'platform', 'verification_passed', 'is_recorded',
        'scheduled_for', 'created_at'
    ]
    
    search_fields = [
        'session_id', 'user__email', 'compliance_request__compliance_id',
        'meeting_id', 'agent__email'
    ]
    
    readonly_fields = [
        'session_id', 'created_at', 'updated_at', 'user_link',
        'compliance_request_link', 'agent_link', 'is_upcoming',
        'time_until_session'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session_id', 'compliance_request_link', 'user_link', 'status', 'purpose')
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'duration_minutes', 'is_upcoming', 'time_until_session')
        }),
        ('Participants', {
            'fields': ('agent_link', 'agent_name', 'agent_title')
        }),
        ('Platform Details', {
            'fields': ('platform', 'meeting_link', 'meeting_id', 'meeting_password')
        }),
        ('Session Data', {
            'fields': ('started_at', 'ended_at', 'actual_duration')
        }),
        ('Recording', {
            'fields': ('is_recorded', 'recording_url', 'recording_duration',
                      'transcription'),
            'classes': ('collapse',)
        }),
        ('Verification Outcome', {
            'fields': ('verification_passed', 'verification_notes', 'issues_identified',
                      'follow_up_required', 'follow_up_notes')
        }),
        ('Notifications', {
            'fields': ('user_notified', 'agent_notified', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('ip_address_user', 'ip_address_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'scheduled_for'
    
    def session_id_short(self, obj):
        return obj.session_id[:12]
    session_id_short.short_description = 'ID'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def compliance_request_link(self, obj):
        if obj.compliance_request:
            url = reverse('admin:compliance_compliancerequest_change', args=[obj.compliance_request.id])
            return format_html('<a href="{}">{}</a>', url, obj.compliance_request.compliance_id[:12])
        return '-'
    compliance_request_link.short_description = 'Compliance Request'
    
    def agent_link(self, obj):
        if obj.agent:
            url = reverse('admin:auth_user_change', args=[obj.agent.id])
            return format_html('<a href="{}">{}</a>', url, obj.agent.email)
        return '-'
    agent_link.short_description = 'Agent'
    
    def status_badge(self, obj):
        status_colors = {
            'scheduled': 'blue',
            'in_progress': 'orange',
            'completed': 'green',
            'cancelled': 'red',
            'missed': 'gray',
            'rescheduled': 'purple',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def platform_display(self, obj):
        return obj.get_platform_display()
    platform_display.short_description = 'Platform'
    
    def verification_passed_badge(self, obj):
        if obj.verification_passed:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">PASSED</span>'
            )
        elif obj.verification_passed is False:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">FAILED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">PENDING</span>'
            )
    verification_passed_badge.short_description = 'Verification'


class ComplianceAuditLogAdmin(admin.ModelAdmin):
    """Admin for Compliance Audit Logs (read-only)"""
    
    list_display = [
        'log_id_short', 'user_email', 'action_short', 'entity_type_display',
        'created_at', 'ip_address_short'
    ]
    
    list_filter = [
        'entity_type', 'action_type', 'created_at'
    ]
    
    search_fields = [
        'log_id', 'user_email', 'entity_id',
        'ip_address'
    ]
    
    readonly_fields = [
        'log_id', 'user_email', 'entity_type',
        'entity_id', 'old_value_prettified', 'new_value_prettified',
        'changed_fields', 'ip_address', 'user_agent', 'location',
        'created_at', 'compliance_request_link', 'kyc_verification_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('log_id', 'user_email', 'action_type')
        }),
        ('Entity Information', {
            'fields': ('entity_type', 'entity_id', 'compliance_request_link',
                      'kyc_verification_link')
        }),
        ('Changes', {
            'fields': ('old_value_prettified', 'new_value_prettified', 'changed_fields')
        }),
        ('Actor Information', {
            'fields': ('actor_id', 'actor_role')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'location', 'notes')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    list_per_page = 100
    date_hierarchy = 'created_at'
    
    def log_id_short(self, obj):
        return obj.log_id[:12]
    log_id_short.short_description = 'ID'
    
    def user_email(self, obj):
        return obj.user_email or 'System'
    user_email.short_description = 'User'
    
    def action_short(self, obj):
        if len(obj.action) > 50:
            return obj.action[:50] + '...'
        return obj.action
    action_short.short_description = 'Action'
    
    def entity_type_display(self, obj):
        return obj.get_entity_type_display()
    entity_type_display.short_description = 'Entity Type'
    
    def ip_address_short(self, obj):
        return obj.ip_address or '-'
    ip_address_short.short_description = 'IP'
    
    def compliance_request_link(self, obj):
        if obj.compliance_request:
            url = reverse('admin:compliance_compliancerequest_change', args=[obj.compliance_request.id])
            return format_html('<a href="{}">{}</a>', url, obj.compliance_request.compliance_id[:12])
        return '-'
    compliance_request_link.short_description = 'Compliance Request'
    
    def kyc_verification_link(self, obj):
        if obj.kyc_verification:
            url = reverse('admin:compliance_kycverification_change', args=[obj.kyc_verification.id])
            return format_html('<a href="{}">{}</a>', url, obj.kyc_verification.kyc_id[:12])
        return '-'
    kyc_verification_link.short_description = 'KYC Verification'
    
    def old_value_prettified(self, obj):
        import json
        if obj.old_value:
            return format_html('<pre>{}</pre>', json.dumps(obj.old_value, indent=2))
        return '-'
    old_value_prettified.short_description = 'Old Value'
    
    def new_value_prettified(self, obj):
        import json
        if obj.new_value:
            return format_html('<pre>{}</pre>', json.dumps(obj.new_value, indent=2))
        return '-'
    new_value_prettified.short_description = 'New Value'
    
    def has_add_permission(self, request):
        """Prevent adding audit logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent changing audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit logs"""
        return False


class ComplianceRuleAdmin(admin.ModelAdmin):
    """Admin for Compliance Rules"""
    
    list_display = [
        'rule_id_short', 'rule_name', 'rule_type_display', 'applicable_apps_display',
        'is_active_badge', 'is_automated_badge', 'priority', 'effective_from'
    ]
    
    list_filter = [
        'rule_type', 'applicable_apps', 'is_active', 'is_automated',
        'effective_from', 'effective_to'
    ]
    
    search_fields = [
        'rule_id', 'rule_name', 'rule_description'
    ]
    
    readonly_fields = [
        'rule_id', 'created_at', 'updated_at', 'is_effective',
    ]
    
    fieldsets = [
        ("Basic Information", {
            "fields": ("rule_id", "rule_name", "rule_description")
        }),
        ("Configuration", {
            "fields": ("rule_type", "applicable_apps", "priority")
        }),
        ("Conditions", {
            "fields": ("condition", "threshold_amount", "threshold_currency",
                      "time_period")
        }),
        ("Actions", {
            "fields": ("action_details",)  # Comma makes it a tuple
        }),
        ("Risk Parameters", {
            "fields": ("risk_weight", "risk_multiplier")
        }),
        ("Status", {
            "fields": ("is_active", "is_automated", "is_effective")
        }),
        ("Metadata", {
            "fields": ("created_by", "notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "effective_from", "effective_to")
        }),
    ]
    
    list_per_page = 50
    
    def rule_id_short(self, obj):
        return obj.rule_id[:12] if obj.rule_id else ""
    rule_id_short.short_description = 'ID'
    
    def rule_type_display(self, obj):
        return obj.get_rule_type_display()
    rule_type_display.short_description = 'Rule Type'
    
    def applicable_apps_display(self, obj):
        return obj.get_applicable_apps_display()
    applicable_apps_display.short_description = 'Apps'
    
    def is_active_badge(self, obj):
        from django.utils.html import format_html
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">ACTIVE</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">INACTIVE</span>'
            )
    is_active_badge.short_description = 'Active'
    
    def is_automated_badge(self, obj):
        from django.utils.html import format_html
        if obj.is_automated:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">AUTO</span>'
            )
        else:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">MANUAL</span>'
            )
    is_automated_badge.short_description = 'Automated'

class ComplianceAlertAdmin(admin.ModelAdmin):
    """Admin for Compliance Alerts"""
    
    list_display = [
        'alert_id_short', 'alert_type_display', 'severity_badge', 'title_short',
        'is_resolved_badge', 'is_acknowledged_badge', 'created_at'
    ]
    
    list_filter = [
        'alert_type', 'severity', 'is_resolved', 'is_acknowledged',
        'created_at', 'expires_at'
    ]
    
    search_fields = [
        'alert_id', 'title', 'description', 'user__email',
        'compliance_request__compliance_id', 'kyc_verification__kyc_id'
    ]
    
    readonly_fields = [
        'alert_id', 'created_at', 'updated_at', 'is_expired', 'user_link',
        'compliance_request_link', 'kyc_verification_link',
        'acknowledged_by_link', 'resolved_by_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('alert_id', 'alert_type', 'severity', 'title', 'description')
        }),
        ('Related Entities', {
            'fields': ('compliance_request_link', 'kyc_verification_link', 'user_link')
        }),
        ('Alert Data', {
            'fields': ('alert_data', 'trigger_conditions'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_resolved', 'is_acknowledged', 'acknowledged_by_link',
                      'acknowledged_at')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'resolved_by_link', 'resolved_at')
        }),
        ('Notification', {
            'fields': ('notified_users', 'notification_sent', 'notification_channels'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at', 'is_expired')
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    actions = ['acknowledge_selected', 'resolve_selected']
    
    def alert_id_short(self, obj):
        return obj.alert_id[:12]
    alert_id_short.short_description = 'ID'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'User'
    
    def compliance_request_link(self, obj):
        if obj.compliance_request:
            url = reverse('admin:compliance_compliancerequest_change', args=[obj.compliance_request.id])
            return format_html('<a href="{}">{}</a>', url, obj.compliance_request.compliance_id[:12])
        return '-'
    compliance_request_link.short_description = 'Compliance Request'
    
    def kyc_verification_link(self, obj):
        if obj.kyc_verification:
            url = reverse('admin:compliance_kycverification_change', args=[obj.kyc_verification.id])
            return format_html('<a href="{}">{}</a>', url, obj.kyc_verification.kyc_id[:12])
        return '-'
    kyc_verification_link.short_description = 'KYC Verification'
    
    def acknowledged_by_link(self, obj):
        if obj.acknowledged_by:
            url = reverse('admin:auth_user_change', args=[obj.acknowledged_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.acknowledged_by.email)
        return '-'
    acknowledged_by_link.short_description = 'Acknowledged By'
    
    def resolved_by_link(self, obj):
        if obj.resolved_by:
            url = reverse('admin:auth_user_change', args=[obj.resolved_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.resolved_by.email)
        return '-'
    resolved_by_link.short_description = 'Resolved By'
    
    def alert_type_display(self, obj):
        return obj.get_alert_type_display()
    alert_type_display.short_description = 'Type'
    
    def severity_badge(self, obj):
        severity_colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred',
        }
        color = severity_colors.get(obj.severity, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_severity_display().upper()
        )
    severity_badge.short_description = 'Severity'
    
    def title_short(self, obj):
        if len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title
    title_short.short_description = 'Title'
    
    def is_resolved_badge(self, obj):
        if obj.is_resolved:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">RESOLVED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">UNRESOLVED</span>'
            )
    is_resolved_badge.short_description = 'Resolved'
    
    def is_acknowledged_badge(self, obj):
        if obj.is_acknowledged:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">ACKNOWLEDGED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">UNACKNOWLEDGED</span>'
            )
    is_acknowledged_badge.short_description = 'Acknowledged'
    
    def acknowledge_selected(self, request, queryset):
        """Acknowledge selected alerts"""
        count = queryset.filter(is_acknowledged=False).update(
            is_acknowledged=True,
            acknowledged_by=request.user,
            acknowledged_at=timezone.now()
        )
        self.message_user(request, f"{count} alerts acknowledged.")
    
    acknowledge_selected.short_description = "Acknowledge selected alerts"
    
    def resolve_selected(self, request, queryset):
        """Resolve selected alerts"""
        count = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now(),
            resolution_notes='Resolved via admin action'
        )
        self.message_user(request, f"{count} alerts resolved.")
    
    resolve_selected.short_description = "Resolve selected alerts"


class ComplianceDashboardStatsAdmin(admin.ModelAdmin):
    """Admin for Dashboard Statistics (read-only)"""
    
    list_display = [
        'period_display', 'total_requests', 'approved_requests',
        'rejected_requests', 'kyc_submissions', 'tac_generated',
        'calculated_at'
    ]
    
    list_filter = [
        'period_type', 'calculated_at'
    ]
    
    search_fields = [
        'period_type'
    ]
    
    readonly_fields = [
        'period_type', 'period_start', 'period_end', 'calculated_at',
        'updated_at', 'all_fields'
    ]
    
    fieldsets = (
        ('Period Information', {
            'fields': ('period_type', 'period_start', 'period_end')
        }),
        ('Statistics', {
            'fields': ('all_fields',)
        }),
        ('Timestamps', {
            'fields': ('calculated_at', 'updated_at')
        }),
    )
    
    list_per_page = 50
    date_hierarchy = 'calculated_at'
    
    def period_display(self, obj):
        return f"{obj.get_period_type_display()} - {obj.period_start.date()} to {obj.period_end.date()}"
    period_display.short_description = 'Period'
    
    def all_fields(self, obj):
        """Display all statistics fields"""
        fields = []
        for field in obj._meta.fields:
            if field.name not in ['id', 'period_type', 'period_start', 'period_end',
                                'calculated_at', 'updated_at', 'requests_per_officer',
                                'avg_resolution_time_per_officer']:
                value = getattr(obj, field.name)
                if value not in [None, 0, 0.0, '', {}, []]:
                    fields.append(f"<strong>{field.verbose_name}:</strong> {value}")
        
        return format_html('<br>'.join(fields))
    all_fields.short_description = 'Statistics'
    
    def has_add_permission(self, request):
        """Prevent adding stats manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent changing stats"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting stats"""
        return False


# Register all models
admin.site.register(ComplianceRequest, ComplianceRequestAdmin)
admin.site.register(KYCVerification, KYCVerificationAdmin)
admin.site.register(KYCDocument, KYCDocumentAdmin)
admin.site.register(TACRequest, TACRequestAdmin)
admin.site.register(VideoCallSession, VideoCallSessionAdmin)
admin.site.register(ComplianceAuditLog, ComplianceAuditLogAdmin)
admin.site.register(ComplianceRule, ComplianceRuleAdmin)
admin.site.register(ComplianceAlert, ComplianceAlertAdmin)
admin.site.register(ComplianceDashboardStats, ComplianceDashboardStatsAdmin)

# Custom admin site configuration
class ComplianceAdminSite(admin.AdminSite):
    """Custom admin site for compliance"""
    site_header = "Compliance Administration"
    site_title = "Compliance Admin Portal"
    index_title = "Compliance Dashboard"
    index_template = "admin/compliance_index.html"

# Uncomment to use custom admin site
# compliance_admin = ComplianceAdminSite(name='compliance_admin')
# compliance_admin.register(ComplianceRequest, ComplianceRequestAdmin)
# ... register other models ...