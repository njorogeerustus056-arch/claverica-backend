from django.db import models
from django.contrib.auth import get_user_model

class TasksTaskcategory(models.Model):
    name = models.CharField(max_length=100, default='')
    description = models.TextField(default='')
    icon = models.CharField(max_length=50, default='')
    color = models.CharField(max_length=20, default='#000000')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tasks_taskcategory'
    
    def __str__(self):
        return self.name

class TasksClavericatask(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    category = models.ForeignKey(TasksTaskcategory, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200, default='')
    description = models.TextField(default='')
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'claverica_tasks_clavericatask'
    
    def __str__(self):
        return self.title

class TasksUserrewardbalance(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    withdrawn_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tasks_userrewardbalance'
    
    def __str__(self):
        return f'{self.user.email if self.user else "No User"}: ${self.available_balance}'
