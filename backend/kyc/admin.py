from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.Documents)
class DocumentsAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.Verifications)
class VerificationsAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
