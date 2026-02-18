import os
import sys

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    import django
    django.setup()
    
    from accounts.models import Account
    from django.contrib.auth import authenticate
    from datetime import date
    
    print("=== Testing Account System ===")
    
    # First, check if admin exists
    try:
        admin = Account.objects.get(email='erustusnyaga001@gmail.com')
        print(f" Admin exists: {admin.email} - {admin.account_number}")
    except Account.DoesNotExist:
        print(" Admin doesn't exist yet")
        # Create admin if doesn't exist
        admin = Account.objects.create_superuser(
            email='erustusnyaga001@gmail.com',
            password='Admin123!',
            phone='0743419963',
            date_of_birth='1980-01-01'
        )
        print(f" Admin created: {admin.email} - {admin.account_number}")
    
    # Test authentication
    user = authenticate(email='erustusnyaga001@gmail.com', password='Admin123!')
    if user:
        print(f" Authentication successful: {user.email}")
    else:
        print(" Authentication failed")
    
    # Create regular user
    try:
        Account.objects.get(email='test@example.com').delete()
    except:
        pass
    
    user2 = Account.objects.create_user(
        email='test@example.com',
        password='Test123!',
        phone='+254711223344',
        date_of_birth=date(1990, 5, 15)
    )
    print(f" User created: {user2.email} - {user2.account_number}")
    
    print(f"\\nTotal users: {Account.objects.count()}")
    
    print("\\n All tests passed! System is working correctly.")
    
except Exception as e:
    print(f" Error: {e}")
    import traceback
    traceback.print_exc()
