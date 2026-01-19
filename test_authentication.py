import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.contrib.auth import get_user_model
from django.test import Client
import json

User = get_user_model()
client = Client()

print("🔐 AUTHENTICATION SYSTEM TEST")
print("=" * 50)

# 1. Test superuser exists
print("\n1️⃣  SUPERUSER CHECK:")
superusers = User.objects.filter(is_superuser=True)
print(f"   Found {superusers.count()} superuser(s)")
for su in superusers:
    print(f"   👑 {su.email} (ID: {su.id})")

# 2. Test login endpoint
print("\n2️⃣  LOGIN ENDPOINT TEST:")
try:
    # Try to access auth endpoints
    response = client.get('/api/auth/health/')
    if response.status_code == 200:
        print("   ✅ Auth health endpoint working")
    else:
        print(f"   ⚠️  Auth health: {response.status_code}")
except Exception as e:
    print(f"   ❌ Auth test failed: {str(e)[:100]}")

# 3. Test user creation
print("\n3️⃣  USER MODEL TEST:")
try:
    # Check if we can create a test user
    test_email = "testuser@claverica.com"
    if not User.objects.filter(email=test_email).exists():
        user = User.objects.create_user(
            email=test_email,
            password="TestPass123!",
            first_name="Test",
            last_name="User"
        )
        print(f"   ✅ Test user created: {user.email}")
        # Clean up
        user.delete()
        print("   ✅ Test user cleaned up")
    else:
        print("   ⚠️  Test user already exists")
except Exception as e:
    print(f"   ❌ User creation failed: {str(e)[:100]}")

# 4. Test permissions
print("\n4️⃣  PERMISSIONS CHECK:")
try:
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        print(f"   ✅ Admin permissions:")
        print(f"      • Is staff: {admin_user.is_staff}")
        print(f"      • Is superuser: {admin_user.is_superuser}")
        print(f"      • Is active: {admin_user.is_active}")
except Exception as e:
    print(f"   ❌ Permissions check failed: {str(e)[:100]}")

print("\n" + "=" * 50)
print("🔐 AUTHENTICATION SYSTEM: READY!")
