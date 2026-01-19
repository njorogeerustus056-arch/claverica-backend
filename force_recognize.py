import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# First, check if we can import each app
apps = ['accounts', 'users', 'cards', 'notifications', 'payments', 
        'transactions', 'transfers']

print("Testing app imports...")
for app in apps:
    try:
        module = __import__(f'backend.{app}')
        print(f"✅ backend.{app} imports")
    except Exception as e:
        print(f"❌ backend.{app}: {str(e)[:50]}")

# Now try Django
try:
    import django
    django.setup()
    print("\n✅ Django setup successful!")
    
    from django.apps import apps
    print(f"Total apps: {len(apps.app_configs)}")
    
except Exception as e:
    print(f"\n❌ Django error: {e}")
