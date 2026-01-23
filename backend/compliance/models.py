from django.db import models
import uuid

class Check(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=255, default='0')
    check_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='pending')
    risk_score = models.FloatField(default=0.0)
    matches_found = models.IntegerField(default=0)
    verification_id = models.UUIDField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    provider = models.CharField(max_length=100, blank=True, null=True)
    provider_reference = models.CharField(max_length=255, blank=True, null=True)
    result = models.JSONField(blank=True, null=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'compliance_checks'
        ordering = ['-checked_at']
    
    def __str__(self):
        return f'{self.check_type} - {self.user_id}'
    
    def save(self, *args, **kwargs):
        # Ensure checked_at is set if not already
        if not self.checked_at:
            from django.utils import timezone
            self.checked_at = timezone.now()
        super().save(*args, **kwargs)
