from django.db import models
from backend.accounts.models import Account
class CryptoAsset(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    class Meta:
        db_table = 'crypto_cryptoasset'
    def __str__(self):
        return f'{self.name} ({self.symbol})'
class Cryptowallet(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, db_column='user_id')
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, db_column='asset_id', null=True, blank=True)
    wallet_address = models.CharField(default='temporary_wallet', max_length=255)
    address = models.CharField(max_length=255, default='unknown')
    wallet_type = models.CharField(max_length=20)
    label = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255, default='Crypto Wallet')
    balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    available_balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    balance_usd = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    private_key_encrypted = models.TextField(default='')
    encrypted_private_key = models.TextField(blank=True, null=True)
    public_key = models.TextField(blank=True, null=True)
    mnemonic_encrypted = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'crypto_cryptowallet'
        verbose_name = 'Crypto Wallet'
        verbose_name_plural = 'Crypto Wallets'
        unique_together = [['user', 'asset']]
    def __str__(self):
        return f'{self.wallet_type} - {self.wallet_address[:10]}...'
class Cryptotransaction(models.Model):
    wallet = models.ForeignKey(Cryptowallet, on_delete=models.CASCADE, db_column='wallet_id', null=True, blank=True)
    transaction_type = models.CharField(max_length=20, default='deposit')
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=0.00000000)
    currency = models.CharField(max_length=10, default='BTC')
    tx_hash = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')
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
