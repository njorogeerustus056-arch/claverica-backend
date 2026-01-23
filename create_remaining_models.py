import os

print("=== CREATING MODELS FOR REMAINING APPS ===")

apps_needing_models = ['tasks', 'compliance', 'tac', 'receipts']

for app in apps_needing_models:
    model_file = f'backend/{app}/models.py'
    
    # Check current content
    with open(model_file, 'r') as f:
        content = f.read()
    
    if len(content.strip()) < 100:  # File is small/empty
        print(f"\n➕ Creating models for {app}")
        
        if app == 'tasks':
            model_content = '''
from django.db import models

class UserTask(models.Model):
    """User tasks from tasks_usertask table"""
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tasks_usertask'
'''
        elif app == 'compliance':
            model_content = '''
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
'''
        elif app == 'tac':
            model_content = '''
from django.db import models

class TacCode(models.Model):
    """TAC (Transaction Authorization Code)"""
    code = models.CharField(max_length=50, unique=True)
    user_id = models.IntegerField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tac_codes'
'''
        elif app == 'receipts':
            model_content = '''
from django.db import models

class Receipt(models.Model):
    """Receipts from receipts_receipt table"""
    user_id = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'receipts_receipt'
'''
        
        with open(model_file, 'w') as f:
            f.write('from django.db import models\n' + model_content)
        
        print(f"✅ Created models for {app}")
    else:
        print(f"📄 {app} already has models")

print("\n🎯 All remaining apps now have models!")
