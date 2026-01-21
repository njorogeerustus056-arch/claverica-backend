from django.contrib import admin
from backend.tasks.models import TaskCategory, ClavericaTask, UserTask, UserRewardBalance

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'

@admin.register(ClavericaTask)
class ClavericaTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'reward_amount', 'status', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'status', 'started_at', 'completed_at', 'reward_earned']
    list_filter = ['status', 'started_at']
    search_fields = ['user__email', 'task__title']
    date_hierarchy = 'started_at'

@admin.register(UserRewardBalance)
class UserRewardBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_earned', 'available_balance', 'withdrawn_balance', 'last_updated']
    search_fields = ['user__email']
    date_hierarchy = 'last_updated'
