from django.db import models
from django.contrib.auth.models import User

class Escrow(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_escrows')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_escrows')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    is_released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Escrow: {self.sender} → {self.receiver} | {self.amount}"
