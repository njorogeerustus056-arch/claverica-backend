import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.db import connection

print("=== CREATING MISSING MODELS ===")

# Tables that need models (from earlier output)
tables_needing_models = [
    'claverica_tasks_clavericatask',
    'claverica_tasks_rewardwithdrawal',
    'claverica_tasks_taskcategory',
    'claverica_tasks_userrewardbalance',
    'escrow_escrow',
    'escrow_escrowlog',
    'kyc_documents',
    'kyc_verifications',
    'crypto_cryptowallet',
    'crypto_cryptotransaction',
    'withdrawal_requests'
]

# Map tables to apps
table_to_app = {
    'claverica_tasks_': 'claverica_tasks',
    'escrow_': 'escrow',
    'kyc_': 'kyc',
    'crypto_': 'crypto',
    'withdrawal_': 'withdrawal'
}

for table in tables_needing_models:
    # Find which app this belongs to
    app_name = None
    for prefix, app in table_to_app.items():
        if table.startswith(prefix):
            app_name = app
            break
    
    if app_name:
        model_file = f'backend/{app_name}/models.py'
        
        # Check if table is already in models
        with open(model_file, 'r') as f:
            content = f.read()
        
        model_name = ''.join(word.title() for word in table.split('_')[1:])
        
        if model_name not in content:
            print(f"➕ Adding {model_name} to {app_name}")
            
            # Add simple model
            with open(model_file, 'a') as f:
                f.write(f'''

class {model_name}(models.Model):
    """
    Model for {table} table
    """
    # TODO: Add fields based on actual table structure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = '{table}'
        verbose_name = '{model_name}'
        verbose_name_plural = '{model_name}s'
''')
        else:
            print(f"✓ {model_name} already in {app_name}")
    else:
        print(f"? {table} - unknown app")

print("\n✅ Models added. Run migrations next!")
