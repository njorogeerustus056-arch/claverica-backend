import sys
import os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.db import connection

# Check columns for key tables
tables_to_check = [
    'claverica_tasks_clavericatask',
    'escrow_escrow',
    'kyc_documents',
    'crypto_cryptowallet',
    'withdrawal_requests'
]

print('📊 TABLE STRUCTURE:')
for table in tables_to_check:
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, [table])
            columns = cursor.fetchall()
            
            if columns:
                print(f'\n{table}:')
                for col in columns[:5]:  # Show first 5 columns
                    print(f'  - {col[0]} ({col[1]})')
                if len(columns) > 5:
                    print(f'  ... and {len(columns)-5} more columns')
            else:
                print(f'\n{table}: No columns found')
    except Exception as e:
        print(f'\n{table}: Error - {str(e)[:50]}')
