from django.db import models

# Models will be auto-generated based on existing database tables


class Cryptowallet(models.Model):
    """
    Model for crypto_cryptowallet table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'crypto_cryptowallet'
        verbose_name = 'Cryptowallet'
        verbose_name_plural = 'Cryptowallets'


class Cryptotransaction(models.Model):
    """
    Model for crypto_cryptotransaction table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'crypto_cryptotransaction'
        verbose_name = 'Cryptotransaction'
        verbose_name_plural = 'Cryptotransactions'
