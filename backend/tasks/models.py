from django.db import models
from django.contrib.auth import get_user_model
from backend.claverica_tasks.models import TasksClavericatask

class UserTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_tasks', db_column='user_id')
    task = models.ForeignKey(TasksClavericatask, on_delete=models.CASCADE, related_name='user_instances')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    metadata = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'tasks_usertask'
        verbose_name = 'User Task'
        verbose_name_plural = 'User Tasks'
        unique_together = ('user', 'task')
    
    def __str__(self):
        return f'{self.user.email if self.user else "No User"} - {self.task.title if self.task else "No Task"}'
