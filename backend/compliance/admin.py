from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
