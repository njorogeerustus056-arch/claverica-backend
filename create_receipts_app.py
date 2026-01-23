import os

app_dir = 'backend/receipts'
if not os.path.exists(app_dir):
    os.makedirs(app_dir, exist_ok=True)
    print(f'📁 Created: {app_dir}')

# Ensure all required files exist
files = {
    '__init__.py': '',
    'apps.py': '''from django.apps import AppConfig

class ReceiptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.receipts'
    verbose_name = 'Receipts'
''',
    'models.py': '''from django.db import models

class Receipt(models.Model):
    # Basic receipt model
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'receipts_receipt'
''',
    'admin.py': '''from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'created_at']
    list_filter = ['created_at']
'''
}

for filename, content in files.items():
    filepath = os.path.join(app_dir, filename)
    
    # Only write if file doesn't exist or is empty
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f'✅ Created: {filename}')
    else:
        print(f'📄 Exists: {filename}')

print('\n🎯 Receipts app ready!')
