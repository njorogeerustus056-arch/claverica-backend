from django.contrib import admin
from .models import Document, Verification

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'document_type', 'uploaded_at')
    search_fields = ('user__email', 'document_type')

@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'created_at')
    search_fields = ('user__email', 'first_name', 'last_name')
