# tasks/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import ClavericaTask, UserTask, TaskCategory, RewardWithdrawal, UserRewardBalance


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']


@admin.register(ClavericaTask)
class ClavericaTaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'task_type', 'reward_amount', 'currency',
        'status', 'current_completions', 'max_completions', 'created_at'
    ]
    list_filter = ['status', 'task_type', 'requires_verification']
    search_fields = ['title', 'description']
    readonly_fields = ['current_completions', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {'fields': ('title', 'description', 'task_type', 'status')}),
        ('Reward Details', {'fields': ('reward_amount', 'currency')}),
        ('Task Settings', {'fields': (
            'estimated_time', 'max_completions', 'current_completions',
            'requires_verification', 'min_account_age_days'
        )}),
        ('Instructions', {'fields': ('instructions',), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('expires_at', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    actions = ['mark_as_active', 'mark_as_inactive', 'mark_as_expired']

    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} task(s) marked as active.')
    mark_as_active.short_description = "Mark selected tasks as active"

    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} task(s) marked as inactive.')
    mark_as_inactive.short_description = "Mark selected tasks as inactive"

    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} task(s) marked as expired.')
    mark_as_expired.short_description = "Mark selected tasks as expired"


@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'status', 'reward_earned', 'reward_paid', 'started_at', 'completed_at']
    list_filter = ['status', 'reward_paid', 'started_at']
    search_fields = ['user__email', 'task__title']
    readonly_fields = ['started_at', 'submitted_at', 'completed_at', 'reviewed_at', 'reward_paid_at']

    fieldsets = (
        ('Task Information', {'fields': ('user', 'task', 'status')}),
        ('Submission', {'fields': ('submission_data', 'submission_notes', 'submitted_at')}),
        ('Reward', {'fields': ('reward_earned', 'reward_paid', 'reward_paid_at')}),
        ('Review', {'fields': ('reviewer', 'review_notes', 'reviewed_at'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('started_at', 'completed_at'), 'classes': ('collapse',)}),
    )

    actions = ['mark_as_completed', 'mark_as_rejected', 'pay_rewards']

    def mark_as_completed(self, request, queryset):
        for user_task in queryset:
            user_task.mark_completed()
        self.message_user(request, f'{queryset.count()} task(s) marked as completed.')
    mark_as_completed.short_description = "Mark selected tasks as completed"

    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} task(s) marked as rejected.')
    mark_as_rejected.short_description = "Mark selected tasks as rejected"

    def pay_rewards(self, request, queryset):
        completed_tasks = queryset.filter(status='completed', reward_paid=False)
        count = 0
        for user_task in completed_tasks:
            user_task.reward_paid = True
            user_task.reward_paid_at = timezone.now()
            user_task.save()
            count += 1
        self.message_user(request, f'{count} reward(s) marked as paid.')
    pay_rewards.short_description = "Mark rewards as paid"


@admin.register(RewardWithdrawal)
class RewardWithdrawalAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'withdrawal_method', 'status', 'requested_at', 'completed_at']
    list_filter = ['status', 'withdrawal_method', 'requested_at']
    search_fields = ['user__email', 'transaction_id']
    readonly_fields = ['requested_at', 'processed_at', 'completed_at']

    fieldsets = (
        ('Withdrawal Information', {'fields': ('user', 'amount', 'currency', 'withdrawal_method')}),
        ('Account Details', {'fields': ('account_details',)}),
        ('Status & Processing', {'fields': ('status', 'transaction_id', 'processor_notes')}),
        ('Timestamps', {'fields': ('requested_at', 'processed_at', 'completed_at'), 'classes': ('collapse',)}),
    )

    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed']

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing', processed_at=timezone.now())
        self.message_user(request, f'{updated} withdrawal(s) marked as processing.')
    mark_as_processing.short_description = "Mark as processing"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} withdrawal(s) marked as completed.')
    mark_as_completed.short_description = "Mark as completed"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} withdrawal(s) marked as failed.')
    mark_as_failed.short_description = "Mark as failed"


@admin.register(UserRewardBalance)
class UserRewardBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'available_balance', 'pending_balance', 'total_earned', 'total_withdrawn', 'tasks_completed']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Balance', {'fields': ('available_balance', 'pending_balance', 'total_earned', 'total_withdrawn', 'currency')}),
        ('Statistics', {'fields': ('tasks_completed', 'tasks_pending')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
