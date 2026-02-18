from django.db import models
from django.utils import timezone

class Notification(models.Model):
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title