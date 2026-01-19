from django.db import models

from django.db import models

class Receipt(models.Model):
    """Receipts from receipts_receipt table"""
    user_id = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'receipts_receipt'
