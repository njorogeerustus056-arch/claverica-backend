from django.contrib import admin
from .models import TasksTaskcategory, TasksClavericatask, TasksUserrewardbalance

@admin.register(TasksTaskcategory)
class TasksTaskcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(TasksClavericatask)
class TasksClavericataskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'reward_amount', 'status', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TasksUserrewardbalance)
class TasksUserrewardbalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('updated_at',)
