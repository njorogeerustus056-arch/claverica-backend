import sys
import os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    import django
    django.setup()
    print('✅ Django setup successful!')
    
    # Try to check tables
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        count = cursor.fetchone()[0]
        print(f'✅ Database connection working: {count} tables')
        
except Exception as e:
    print(f'❌ Error: {e}')
