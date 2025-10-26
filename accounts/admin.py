from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'balance', 'verified')
    search_fields = ('user__username', 'phone_number')
    list_filter = ('verified',)
