from django.contrib import admin
from django.utils import timezone
from .models import KYCDocument, KYCSubmission, KYCSetting
from django.utils.html import format_html

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'document_type', 'status_badge', 'submitted_at', 'reviewed_at', 'expires_soon')
    list_filter = ('status', 'document_type', 'submitted_at')
    search_fields = ('user__email', 'user__account_number', 'admin_notes')
    readonly_fields = ('submitted_at',)
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'document_type')
        }),
        ('Document Images', {
            'fields': ('id_front_image', 'id_back_image', 'facial_image'),
            'description': 'Uploaded document images'
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes', 'rejection_reason')
        }),
        ('System Information', {
            'fields': ('submitted_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['approve_selected', 'reject_selected', 'mark_for_correction']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'under_review': 'blue',
            'approved': 'green',
            'rejected': 'red',
            'needs_correction': 'yellow',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def expires_soon(self, obj):
        if obj.expires_at:
            days_left = (obj.expires_at - timezone.now()).days
            if days_left < 7:
                return format_html('<span style="color: red;">{} days left</span>', days_left)
            elif days_left < 30:
                return format_html('<span style="color: orange;">{} days left</span>', days_left)
            return f"{days_left} days left"
        return "N/A"
    expires_soon.short_description = 'Expires In'
    
    def approve_selected(self, request, queryset):
        updated = queryset.update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            admin_notes=f'Approved by admin {request.user.email} on {timezone.now().strftime("%Y-%m-%d %H:%M")}'
        )
        self.message_user(request, f"{updated} KYC document(s) approved.")
    approve_selected.short_description = "Approve selected KYC documents"
    
    def reject_selected(self, request, queryset):
        for obj in queryset:
            obj.status = 'rejected'
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
        self.message_user(request, f"{queryset.count()} KYC document(s) rejected.")
    reject_selected.short_description = "Reject selected KYC documents"
    
    def mark_for_correction(self, request, queryset):
        for obj in queryset:
            obj.status = 'needs_correction'
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
        self.message_user(request, f"{queryset.count()} KYC document(s) marked for correction.")
    mark_for_correction.short_description = "Mark selected for correction"

@admin.register(KYCSubmission)
class KYCSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'service_type', 'requested_for', 'is_completed', 'created_at')
    list_filter = ('service_type', 'is_completed', 'created_at')
    search_fields = ('user__email', 'requested_for')
    readonly_fields = ('created_at', 'completed_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

@admin.register(KYCSetting)
class KYCSettingAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'requires_kyc', 'threshold_amount', 'is_active')
    list_editable = ('requires_kyc', 'threshold_amount', 'is_active')
    list_filter = ('is_active', 'requires_kyc')
