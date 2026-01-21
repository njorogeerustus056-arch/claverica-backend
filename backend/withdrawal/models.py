from django.db import models
from django.conf import settings
import uuid

class Requests(models.Model):
    """
    Model for withdrawal_requests table
    MATCHING ACTUAL DATABASE SCHEMA
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # user_id is VARCHAR, not ForeignKey in the database
    user_id = models.CharField(max_length=255)
    
    # amount is double precision in DB
    amount = models.FloatField()  # Double precision
    
    currency = models.CharField(max_length=10)
    destination_type = models.CharField(max_length=100)
    destination_details = models.JSONField()
    
    status = models.CharField(max_length=50)
    requires_tac = models.BooleanField()
    tac_verified = models.BooleanField()
    tac_code_id = models.CharField(max_length=255, null=True, blank=True)
    kyc_status = models.CharField(max_length=50, null=True, blank=True)
    compliance_status = models.CharField(max_length=50)
    processed_by = models.CharField(max_length=255, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    transaction_hash = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True, default='Withdrawal Request')
    
    class Meta:
        db_table = 'withdrawal_requests'
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
        ordering = ['-created_at']
        app_label = 'withdrawal'
    
    def __str__(self):
        return f'Withdrawal #{self.id}: ${self.amount} {self.currency}'
    
    # Property to get user object (if needed)
    @property
    def user(self):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            return User.objects.get(id=self.user_id)
        except:
            return None
