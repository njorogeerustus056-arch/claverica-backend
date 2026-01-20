from django.db import models
from django.contrib.auth import get_user_model

class TasksTaskcategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fa-tasks')
    color = models.CharField(max_length=50, default='#007bff')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claverica_tasks_taskcategory'
        verbose_name = 'Task Category'
        verbose_name_plural = 'Task Categories'
    
    def __str__(self):
        return self.name

class TasksUserrewardbalance(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='reward_balance', db_column='user_id')
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    tasks_completed = models.IntegerField(default=0)
    tasks_pending = models.IntegerField(default=0)
    name = models.CharField(max_length=255, default='User Balance', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claverica_tasks_userrewardbalance'
        verbose_name = 'User Reward Balance'
        verbose_name_plural = 'User Reward Balances'
    
    def __str__(self):
        return f'{self.user.email if self.user else "No User"}\'s Balance'

class TasksClavericatask(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed'), ('expired', 'Expired')]
    TASK_TYPE_CHOICES = [('survey', 'Survey'), ('watch_video', 'Watch Video'), ('install_app', 'Install App'), ('sign_up', 'Sign Up'), ('quiz', 'Quiz'), ('other', 'Other')]
    
    title = models.CharField(max_length=255, default='Untitled Task')
    description = models.TextField(default='No description provided')
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='survey')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    estimated_time = models.IntegerField(default=5)
    max_completions = models.IntegerField(blank=True, null=True)
    current_completions = models.IntegerField(default=0)
    requires_verification = models.BooleanField(default=False)
    min_account_age_days = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    instructions = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=255, default='Claverica Task', blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claverica_tasks_clavericatask'
        verbose_name = 'Claverica Task'
        verbose_name_plural = 'Claverica Tasks'
    
    def __str__(self):
        return self.title

class TasksRewardwithdrawal(models.Model):
    name = models.CharField(max_length=255, default='Reward Withdrawal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claverica_tasks_rewardwithdrawal'
        verbose_name = 'Reward Withdrawal'
        verbose_name_plural = 'Reward Withdrawals'
# Fix verified at Tue Jan 20 21:44:03 UTC 2026
