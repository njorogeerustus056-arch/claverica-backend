# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Account  # Changed from User to Account


@admin.register(Account)
class AccountAdmin(BaseUserAdmin):  # Changed from UserAdmin to AccountAdmin
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'email_verified', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'email_verified', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Verification'), {'fields': ('email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )