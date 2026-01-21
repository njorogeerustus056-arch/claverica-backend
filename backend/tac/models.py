from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

class TacCode(models.Model):
    PURPOSE_CHOICES = [
        ('verification', 'Verification'),
        ('withdrawal', 'Withdrawal'),
        ('login', 'Login'),
        ('transaction', 'Transaction'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='tac_codes', db_column='user_id')
    code = models.CharField(max_length=6, unique=True, default='')
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='verification')
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tac_codes'
        verbose_name = 'TAC Code'
        verbose_name_plural = 'TAC Codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.code} - {self.user.email if self.user else "No User"}'
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at