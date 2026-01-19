from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.TacCode)
class TacCodeAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
