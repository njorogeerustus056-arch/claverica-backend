from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
