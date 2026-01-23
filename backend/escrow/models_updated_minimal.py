from django.db import models
import uuid

class Escrow(models.Model):
    # Existing fields from current model
    name = models.CharField(max_length=255, default='')
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=50, default='pending')
    
    # Add missing critical fields that exist in DB
    metadata = models.JSONField(default=dict, blank=True)  # This fixes the current error
    
    # Optional: Add other critical fields that might be needed
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'escrow_escrow'
    
    def __str__(self):
        return f"{self.name} (${self.amount})"
