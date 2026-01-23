import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.db import connection, transaction

print("🔧 QUICK DATABASE FIX")
print("=" * 50)

# List of problematic tables from tests
problem_tables = [
    'payments_payment',
    'transfers_transferrequest', 
    'transfers_transferlimit'
]

print("\n🔍 CHECKING PROBLEM TABLES:")
with connection.cursor() as cursor:
    for table in problem_tables:
        try:
            cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
            exists = cursor.fetchone()[0]
            if exists:
                print(f"   ✅ {table}: EXISTS")
                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"      Records: {count}")
            else:
                print(f"   ❌ {table}: MISSING")
                
                # Try to create if simple structure known
                if table == 'payments_payment':
                    print(f"      Attempting to create via migrations...")
                elif table == 'transfers_transferrequest':
                    print(f"      Attempting to create via migrations...")
                elif table == 'transfers_transferlimit':
                    print(f"      Attempting to create via migrations...")
                    
        except Exception as e:
            print(f"   💥 {table}: Error - {str(e)[:80]}")

print("\n🎯 RECOMMENDED ACTION:")
print("""
   Since you're on Render with a production database:
   
   1. Check if these tables are actually needed:
      - Review your models in backend/payments/models.py
      - Review your models in backend/transfers/models.py
   
   2. If they ARE needed, run:
      python manage.py makemigrations payments transfers
      python manage.py migrate payments transfers
   
   3. If they're NOT needed (old models), remove from admin registration
""")
