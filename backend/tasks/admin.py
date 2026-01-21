from django.contrib import admin
from .models import TaskCategory, ClavericaTask, UserTask, UserRewardBalance

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active', 'display_order']

@admin.register(ClavericaTask)
class ClavericaTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'reward_amount', 'status', 'created_at']

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'status', 'reward_earned', 'started_at']
    readonly_fields = ('started_at', 'completed_at')  # ✅ VISIBLE FIX

@admin.register(UserRewardBalance)
class UserRewardBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_earned', 'total_withdrawn', 'available_balance', 'pending_balance', 'currency']
    # ✅ Now shows all database fields correctly
