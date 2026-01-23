import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('.')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model
User = get_user_model()

print("=== Database check ===")
try:
    # Test connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print(f"✅ Database connection: {cursor.fetchone()}")
    
    # Check if admin exists
    admin_count = User.objects.filter(email='admin@claverica.com').count()
    print(f"✅ Admin users: {admin_count}")
    
    if admin_count > 0:
        admin = User.objects.get(email='admin@claverica.com')
        print(f"   Admin ID: {admin.id}")
        print(f"   Is active: {admin.is_active}")
        print(f"   Is superuser: {admin.is_superuser}")
    
except Exception as e:
    print(f"❌ Database error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
