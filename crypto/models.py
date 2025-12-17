from django.db import models
from django.contrib.auth.models import User

class CryptoCurrency(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    is_active = models.BooleanField(default=True)
    last_price_update = models.DateTimeField(auto_now=True)

class CryptoWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    available_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    def get_usd_value(self):
        return self.balance * self.currency.current_price

class CryptoTransaction(models.Model):
    from_wallet = models.ForeignKey(CryptoWallet, on_delete=models.CASCADE, related_name='sent_transactions')
    to_wallet = models.ForeignKey(CryptoWallet, on_delete=models.CASCADE, related_name='received_transactions', null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    status = models.CharField(max_length=20, default='pending')
    transaction_type = models.CharField(max_length=20, default='transfer')
    confirmations = models.IntegerField(default=0)
    tx_hash = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class CryptoAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE)
    address = models.CharField(max_length=100)
    label = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)

class ExchangeRate(models.Model):
    from_currency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE, related_name='exchange_from')
    to_currency = models.ForeignKey(CryptoCurrency, on_delete=models.CASCADE, related_name='exchange_to')
    rate = models.DecimalField(max_digits=20, decimal_places=8)
    last_updated = models.DateTimeField(auto_now=True)
