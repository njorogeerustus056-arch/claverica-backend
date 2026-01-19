from django.db import models

# Models will be auto-generated based on existing database tables


class Escrow(models.Model):
    """
    Model for escrow_escrow table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'escrow_escrow'
        verbose_name = 'Escrow'
        verbose_name_plural = 'Escrows'


class Escrowlog(models.Model):
    """
    Model for escrow_escrowlog table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'escrow_escrowlog'
        verbose_name = 'Escrowlog'
        verbose_name_plural = 'Escrowlogs'
