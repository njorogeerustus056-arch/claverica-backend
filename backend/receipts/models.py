from django.db import models
from backend.accounts.models import Account

class Receipt(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='receipts')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=50, default='pending')
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    receipt_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt #{self.id} - {self.user.email} (${self.amount})"
