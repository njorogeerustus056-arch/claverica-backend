from django.db import models
from django.conf import settings

class TasksTaskcategory(models.Model):
    name = models.CharField(max_length=100, unique=True, default='')
    icon = models.CharField(max_length=50, default='question-circle')
    color = models.CharField(max_length=20, default='#000000')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claverica_tasks_taskcategory'
        verbose_name = 'Task Category'
        verbose_name_plural = 'Task Categories'
    
    def __str__(self):
        return self.name

class TasksClavericatask(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200, default='')
    description = models.TextField(default='')
    category = models.ForeignKey(TasksTaskcategory, on_delete=models.SET_NULL, null=True, blank=True)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claverica_tasks_clavericatask'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return self.title

class TasksUserrewardbalance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id')
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'claverica_tasks_userrewardbalance'
        verbose_name = 'User Reward Balance'
        verbose_name_plural = 'User Reward Balances'
    
    def __str__(self):
        return f'{self.user.email if self.user else "No User"} - {self.balance}'
