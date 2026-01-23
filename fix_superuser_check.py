import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

print("👑 CHECKING SUPERUSER:")

if User.objects.filter(is_superuser=True).exists():
    admin = User.objects.filter(is_superuser=True).first()
    print("✅ Superuser exists!")
    
    # Check what fields exist
    print(f"   ID: {admin.id}")
    print(f"   Email: {admin.email}")
    
    # Check common fields
    if hasattr(admin, 'username'):
        print(f"   Username: {admin.username}")
    if hasattr(admin, 'first_name'):
        print(f"   First name: {admin.first_name}")
    if hasattr(admin, 'last_name'):
        print(f"   Last name: {admin.last_name}")
        
    print(f"   Is active: {admin.is_active}")
    print(f"   Is staff: {admin.is_staff}")
    print(f"   Is superuser: {admin.is_superuser}")
else:
    print("❌ No superuser found")
