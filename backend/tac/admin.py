from django.contrib import admin
from .models import TacCode

@admin.register(TacCode)
class TacCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'purpose', 'is_used', 'created_at', 'expires_at')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('code', 'user__email', 'user__username')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('TAC Code Information', {
            'fields': ('user', 'code', 'purpose', 'is_used')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
