from django.contrib import admin
from .models import TaskCategory, ClavericaTask, UserTask, UserRewardBalance

# ✅ VISIBLE CHANGE: Added readonly_fields to UserTaskAdmin
@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'task', 'status', 'reward_earned', 'started_at')
    readonly_fields = ('started_at', 'completed_at')  # ✅ Added readonly_fields
    list_filter = ('status',)
    search_fields = ('user__email', 'task__title')

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'is_active', 'display_order')

@admin.register(ClavericaTask)
class ClavericaTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'reward_amount', 'status')

@admin.register(UserRewardBalance)
class UserRewardBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_earned', 'available_balance', 'currency')
