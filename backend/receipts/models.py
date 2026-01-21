from django.db import models
from django.contrib.auth import get_user_model

class Receipt(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, db_column='user_id')
    transaction_id = models.CharField(max_length=100, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(default='')
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'receipts'
        db_table = 'receipts_receipt'
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Receipt #{self.id} - {self.amount} {self.currency}'
