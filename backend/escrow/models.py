from django.db import models
import time

class Escrow(models.Model):
    escrow_id = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, default="Test Escrow")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "escrow_final"
    
    def __str__(self):
        return f"{self.title} ({self.escrow_id})"
    
    def save(self, *args, **kwargs):
        if not self.escrow_id:
            self.escrow_id = f'ESC-{int(time.time())}'
        super().save(*args, **kwargs)

class Escrowlog(models.Model):
    escrow = models.ForeignKey(Escrow, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=255, default='')
    details = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = "escrow_final"
    
    def __str__(self):
        return f"Log: {self.escrow.escrow_id} - {self.action}"
