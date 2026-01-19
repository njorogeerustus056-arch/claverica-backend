import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    import django
    django.setup()
    print("✅ Django setup!")
    
    # Check apps
    from django.apps import apps
    backend = [a for a in apps.app_configs if 'backend' in a]
    print(f"Backend apps found: {len(backend)}")
    for app in sorted(backend)[:10]:
        print(f"  - {app}")
        
except Exception as e:
    print(f"❌ Error: {e}")
