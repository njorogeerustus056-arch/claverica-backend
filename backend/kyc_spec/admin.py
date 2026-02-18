from django.contrib import admin
from .models import KycSpecDump

@admin.register(KycSpecDump)
class KycSpecDumpAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_type', 'user_email', 'document_count', 'status', 'created_at')
    list_filter = ('product_type', 'status', 'created_at')
    search_fields = ('user_email', 'user_phone', 'raw_data')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'product_type', 'product_subtype', 'status')
        }),
        ('User Info', {
            'fields': ('user', 'user_email', 'user_phone')
        }),
        ('Data', {
            'fields': ('raw_data', 'document_count')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'source', 'created_at', 'updated_at')
        }),
    )
