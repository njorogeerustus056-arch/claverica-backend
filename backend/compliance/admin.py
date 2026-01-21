from django.contrib import admin
from .models import Check

@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ['check_type', 'user_id', 'status', 'risk_score', 'checked_at']
    list_filter = ['status', 'check_type']
    search_fields = ['user_id', 'name']
    readonly_fields = ['checked_at', 'created_at']
    
    fieldsets = (
        ('Check Information', {
            'fields': ('check_type', 'user_id', 'status', 'risk_score', 'matches_found')
        }),
        ('Details', {
            'fields': ('verification_id', 'name', 'notes', 'provider', 'provider_reference'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('result',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('checked_at', 'created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
