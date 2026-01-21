from django.contrib import admin
from .models import UserTask

@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user_email', 'get_task_display', 'status', 'get_reward_display', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at', 'completed_at')
    search_fields = ('user__email', 'task__name', 'metadata')
    readonly_fields = ('id', 'metadata')
    list_per_page = 20
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else 'No user'
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'
    
    def get_task_display(self, obj):
        if obj.task and hasattr(obj.task, 'name'):
            return obj.task.name
        elif obj.metadata and 'task_name' in obj.metadata:
            return obj.metadata.get('task_name', 'Task')
        else:
            return f'Task #{obj.id}'
    get_task_display.short_description = 'Task'
    
    def get_reward_display(self, obj):
        if hasattr(obj, 'reward_earned'):
            return f'${obj.reward_earned}'
        elif obj.metadata and 'reward' in obj.metadata:
            return f'${obj.metadata.get("reward", 0)}'
        else:
            return 'N/A'
    get_reward_display.short_description = 'Reward'
    
    fieldsets = (
        ('Task Information', {
            'fields': ('user', 'task', 'status', 'metadata')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Rewards', {
            'fields': ('reward_earned',)
        }),
    )
