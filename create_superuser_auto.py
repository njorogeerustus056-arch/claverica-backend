import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("👑 CREATING SUPERUSER:")

# Check if superuser exists
if User.objects.filter(is_superuser=True).exists():
    print("✅ Superuser already exists")
    admin = User.objects.filter(is_superuser=True).first()
    print(f"   Username: {admin.username}")
    print(f"   Email: {admin.email}")
else:
    print("🛠️ Creating default superuser...")
    try:
        # Create superuser
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@claverica.com',
            password='admin123'
        )
        print("✅ Superuser created!")
        print("   Username: admin")
        print("   Email: admin@claverica.com")
        print("   Password: admin123")
        print("\n⚠️ CHANGE THIS PASSWORD IMMEDIATELY!")
    except Exception as e:
        print(f"❌ Could not create superuser: {e}")
        print("\n📝 Run manually: python manage.py createsuperuser")
