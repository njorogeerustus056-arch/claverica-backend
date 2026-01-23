import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

# Check users
users = User.objects.all()
print("All users:")
for u in users:
    print(f"  {u.id}: {u.email} - Active: {u.is_active}")

# Test authentication
test_users = [
    ("erustusnyaga001@gmail.com", "NewPassword123"),
    ("admin@claverica.com", "Admin123!"),
]

for email, password in test_users:
    print(f"\nTrying: {email}")
    user = authenticate(email=email, password=password)
    if user:
        print(f"  ✅ Authenticated: {user.email}")
    else:
        print(f"  ❌ Authentication failed")
        # Check password directly
        try:
            u = User.objects.get(email=email)
            print(f"  Password check: {u.check_password(password)}")
        except:
            print(f"  User not found")
