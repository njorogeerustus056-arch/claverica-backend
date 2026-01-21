from django.db import models

class Escrow(models.Model):
    # Minimal required fields based on database schema
    name = models.CharField(max_length=255, default='')
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=50, default='pending')
    metadata = models.JSONField(default=dict, blank=True)
    
    # Optional fields that exist in database
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'escrow_escrow'
    
    def __str__(self):
        return f"{self.name} (${self.amount})"
