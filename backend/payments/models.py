
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Account(models.Model):
    class Meta:
        app_label = "payments"
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_account")
    account_number = models.CharField(max_length=50, unique=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.account_number} - {self.user.email}"

class Card(models.Model):
    class Meta:
        app_label = "payments"
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_cards")
    card_number = models.CharField(max_length=20)
    card_type = models.CharField(max_length=20, default="debit")
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Card {self.card_number[-4:]}"

class PaymentMethod(models.Model):
    class Meta:
        app_label = "payments"
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    method_type = models.CharField(max_length=50)
    details = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.method_type} - {self.user.email}"

class Payment(models.Model):
    class Meta:
        app_label = "payments"
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment #{self.id}: ${self.amount}"

class Transaction(models.Model):
    class Meta:
        app_label = "payments"
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type}: ${self.amount}"
