import sys
import os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.db import connection

# Map for common apps
app_tables = {
    'claverica_tasks': ['claverica_tasks_clavericatask', 'claverica_tasks_rewardwithdrawal', 
                       'claverica_tasks_taskcategory', 'claverica_tasks_userrewardbalance'],
    'escrow': ['escrow_escrow', 'escrow_escrowlog'],
    'kyc': ['kyc_documents', 'kyc_verifications'],
    'crypto': ['crypto_cryptowallet', 'crypto_cryptotransaction'],
    'withdrawal': ['withdrawal_requests']
}

print('🔧 Creating models from database...')

for app, tables in app_tables.items():
    models_file = f'backend/{app}/models.py'
    
    content = 'from django.db import models\n\n'
    
    for table in tables:
        # Get columns
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
            """, [table])
            columns = cursor.fetchall()
        
        # Create model name
        model_name = ''.join(word.title() for word in table.split('_')[1:])
        
        content += f'class {model_name}(models.Model):\n'
        
        # Add basic fields based on column names
        field_added = False
        for col_name, data_type in columns:
            if col_name == 'id':
                continue
            
            # Simple field mapping
            if 'int' in data_type:
                field = f'    {col_name} = models.IntegerField()'
            elif 'char' in data_type or 'text' in data_type:
                field = f'    {col_name} = models.CharField(max_length=255)'
            elif 'bool' in data_type:
                field = f'    {col_name} = models.BooleanField(default=False)'
            elif 'timestamp' in data_type or 'date' in data_type:
                field = f'    {col_name} = models.DateTimeField(auto_now_add=True)'
            elif 'numeric' in data_type or 'decimal' in data_type:
                field = f'    {col_name} = models.DecimalField(max_digits=10, decimal_places=2)'
            else:
                field = f'    {col_name} = models.CharField(max_length=255)'
            
            content += field + '\n'
            field_added = True
        
        if not field_added:
            content += '    pass\n'
        
        content += '\n' + f'    class Meta:\n'
        content += f'        db_table = \'{table}\'\n'
        content += f'        ordering = [\'id\']\n\n'
    
    # Write the file
    with open(models_file, 'w') as f:
        f.write(content)
    
    print(f'✅ Created models for {app} ({len(tables)} tables)')
