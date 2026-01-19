from django.contrib import admin
from . import models

# Register your models here

@admin.register(models.TasksClavericatask)
class TasksClavericataskAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.TasksRewardwithdrawal)
class TasksRewardwithdrawalAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.TasksTaskcategory)
class TasksTaskcategoryAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    

@admin.register(models.TasksUserrewardbalance)
class TasksUserrewardbalanceAdmin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
