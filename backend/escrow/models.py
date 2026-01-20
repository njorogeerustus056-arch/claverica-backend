from django.db import models
from django.conf import settings

class Escrow(models.Model):
    class Meta:
        app_label = "escrow"
    
    name = models.CharField(max_length=255, default='')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Escrow: {self.name}"

class Escrowlog(models.Model):
    class Meta:
        app_label = "escrow"
    
    escrow = models.ForeignKey(Escrow, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=255, default='')
    details = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Log: {self.escrow.name} - {self.action}"
