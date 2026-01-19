from django.db import models

# Models will be auto-generated based on existing database tables


class Requests(models.Model):
    """
    Model for withdrawal_requests table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        verbose_name = 'Requests'
        verbose_name_plural = 'Requestss'
