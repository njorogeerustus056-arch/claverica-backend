import os
import sys

# Setup Django
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.contrib.auth import authenticate
from accounts.models import Account

print("=== Testing Authentication with YOUR Password ===")

# Test with YOUR actual password: 38876879Eruz
user = authenticate(email='erustusnyaga001@gmail.com', password='38876879Eruz')
if user:
    print(f"✅ Authentication SUCCESSFUL!")
    print(f"   User: {user.email}")
    print(f"   Account: {user.account_number}")
    print(f"   Superuser: {user.is_superuser}")
else:
    print("❌ Authentication FAILED")
    print("   Trying with Admin123!...")
    
    # Try with Admin123! (in case you want to reset)
    user2 = authenticate(email='erustusnyaga001@gmail.com', password='Admin123!')
    if user2:
        print("   ✅ Admin123! works (password was reset earlier)")
    else:
        print("   ❌ Admin123! also doesn't work")

# Test with test user
test_user = authenticate(email='test@example.com', password='Test123!')
if test_user:
    print(f"✅ Test user authentication: SUCCESS")
else:
    print(f"❌ Test user authentication: FAILED")
