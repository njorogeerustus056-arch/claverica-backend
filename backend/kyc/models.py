from django.db import models

# Models will be auto-generated based on existing database tables


class Documents(models.Model):
    """
    Model for kyc_documents table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kyc_documents'
        verbose_name = 'Documents'
        verbose_name_plural = 'Documentss'


class Verifications(models.Model):
    """
    Model for kyc_verifications table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kyc_verifications'
        verbose_name = 'Verifications'
        verbose_name_plural = 'Verificationss'
