import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claverica.settings')
django.setup()

from django.apps import apps

# Find the Account model
try:
    Account = apps.get_model('accounts', 'Account')
    print("🔍 Account model fields:")
    print("=" * 50)
    
    for field in Account._meta.get_fields():
        print(f"  • {field.name} ({field.__class__.__name__})")
    
    print(f"\n📊 Total fields: {len(list(Account._meta.get_fields()))}")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Check if the problematic fields exist in database
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='accounts_account'
        ORDER BY ordinal_position
    """)
    print("\n🗄️  Database columns for accounts_account:")
    print("=" * 50)
    for col_name, data_type in cursor.fetchall():
        print(f"  • {col_name}: {data_type}")
