from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.Escrowlog)
class EscrowlogAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
