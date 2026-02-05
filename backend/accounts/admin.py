from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

class AccountAdmin(UserAdmin):
    list_display = ('email', 'account_number', 'first_name', 'last_name', 'phone', 'is_staff', 'is_verified', 'kyc_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified', 'kyc_status', 'account_status')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'gender')}),
        ('KYC Information', {'fields': ('doc_type', 'doc_number', 'doc_country', 'doc_expiry_date', 
                                       'doc_front_image', 'doc_back_image', 'doc_selfie_image')}),
        ('Address Information', {'fields': ('address_line1', 'address_line2', 'city', 'state_province', 
                                           'postal_code', 'country', 'country_of_residence', 'nationality')}),
        ('Employment Information', {'fields': ('occupation', 'employer', 'income_range')}),
        ('Account Information', {'fields': ('account_number', 'is_verified', 'account_status', 
                                           'kyc_status', 'risk_level', 'activation_code', 
                                           'activation_code_sent_at', 'activation_code_expires_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
        }),
    )
    
    search_fields = ('email', 'account_number', 'first_name', 'last_name', 'phone', 'doc_number')
    ordering = ('email',)
    readonly_fields = ('account_number', 'date_joined', 'last_login', 'created_at', 'updated_at')

admin.site.register(Account, AccountAdmin)
