from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.Cryptowallet)
class CryptowalletAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.Cryptotransaction)
class CryptotransactionAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
