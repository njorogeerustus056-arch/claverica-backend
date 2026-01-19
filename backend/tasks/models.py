from django.db import models

from django.db import models

class UserTask(models.Model):
    """User tasks from tasks_usertask table"""
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tasks_usertask'
