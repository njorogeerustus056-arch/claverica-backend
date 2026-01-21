from django.contrib import admin

# Customize the admin site appearance
admin.site.site_header = "Claverica Administration"
admin.site.site_title = "Claverica Admin Portal"
admin.site.index_title = "Welcome to the Claverica Dashboard"

# Escrow Admin
from backend.escrow.models import Escrow

@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ('escrow_id', 'title', 'amount', 'created_at')
