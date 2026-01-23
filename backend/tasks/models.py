from django.db import models
from django.contrib.auth import get_user_model

class TaskCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50)
    color = models.CharField(max_length=50, default='#000000')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'tasks'
        db_table = 'claverica_tasks_taskcategory'
        verbose_name = 'Task Category'
        verbose_name_plural = 'Task Categories'

    def __str__(self):
        return self.name

class ClavericaTask(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200, default='')
    description = models.TextField(default='')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'tasks'
        db_table = 'claverica_tasks_clavericatask'
        verbose_name = 'Claverica Task'
        verbose_name_plural = 'Claverica Tasks'

    def __str__(self):
        return self.title

class UserTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_tasks', db_column='user_id')
    task = models.ForeignKey(ClavericaTask, on_delete=models.CASCADE, related_name='user_instances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        app_label = 'tasks'
        db_table = 'claverica_tasks_usertask'
        verbose_name = 'User Task'
        verbose_name_plural = 'User Tasks'
        unique_together = ('user', 'task')

    def __str__(self):
        if self.user and self.task:
            return f'{self.user.email} - {self.task.title}'
        elif self.task:
            return f'No User - {self.task.title}'
        else:
            return 'No Task'


class UserRewardBalance(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='reward_balance')
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    tasks_completed = models.IntegerField(default=0)
    tasks_pending = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255, default='User Balance')

    class Meta:
        app_label = 'tasks'
        db_table = 'claverica_tasks_userrewardbalance'
        verbose_name = 'User Reward Balance'
        verbose_name_plural = 'User Reward Balances'

    def __str__(self):
        if self.user:
            return f'{self.user.email}: $' + str(self.available_balance)
        else:
            return 'No User'
