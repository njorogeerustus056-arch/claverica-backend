from django.db import models

from django.db import models

class AuditLog(models.Model):
    """Compliance audit logs"""
    action = models.CharField(max_length=255)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_audit_logs'

class Check(models.Model):
    """Compliance checks"""
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'compliance_checks'

class Profile(models.Model):
    """Compliance profiles"""
    user_id = models.IntegerField()
    level = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'compliance_profiles'
