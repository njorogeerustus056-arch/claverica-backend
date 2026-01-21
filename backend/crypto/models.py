from django.db import models
from django.contrib.auth import get_user_model

class Cryptowallet(models.Model):
    WALLET_TYPES = [
        ('bitcoin', 'Bitcoin'),
        ('ethereum', 'Ethereum'),
        ('litecoin', 'Litecoin'),
        ('tron', 'Tron'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, db_column='user_id')
    wallet_type = models.CharField(max_length=20, choices=WALLET_TYPES, default='bitcoin')
    address = models.CharField(max_length=255, unique=True, default='')
    private_key_encrypted = models.TextField(default='')
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_cryptowallet'
        verbose_name = 'Crypto Wallet'
        verbose_name_plural = 'Crypto Wallets'
    
    def __str__(self):
        return f'{self.wallet_type} - {self.address[:10]}...'

class Cryptotransaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(Cryptowallet, on_delete=models.CASCADE, db_column='wallet_id', null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='deposit')
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)
    currency = models.CharField(max_length=10, default='BTC')
    tx_hash = models.CharField(max_length=255, unique=True, null=True, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    from_address = models.CharField(max_length=255, default='')
    to_address = models.CharField(max_length=255, default='')
    fee = models.DecimalField(max_digits=10, decimal_places=8, default=0.00000000)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'crypto_cryptotransaction'
        verbose_name = 'Crypto Transaction'
        verbose_name_plural = 'Crypto Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.transaction_type} - {self.amount} {self.currency}'
