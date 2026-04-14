# receipts/admin.py
from django.contrib import admin

from .models import Receipt


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin configuration for the Receipt model."""

    list_display = ["id", "type", "amount", "customer_name", "date", "uploaded_at", "uploaded_by"]
    list_filter = ["type", "date", "uploaded_at"]
    search_fields = ["customer_name", "type"]
    readonly_fields = ["uploaded_at", "uploaded_by"]
    ordering = ["-date", "-uploaded_at"]

    def save_model(self, request, obj, form, change):
        """Automatically set uploaded_by to the current admin user on create."""
        if not obj.pk:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)