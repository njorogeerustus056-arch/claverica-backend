import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    import django
    django.setup()
    from django.apps import apps
    
    print("✅ Django apps loaded:")
    backend = [a for a in apps.app_configs if a.startswith('backend.')]
    for app in sorted(backend):
        print(f"  - {app}")
    print(f"\n🎯 Total: {len(backend)} backend apps")
except Exception as e:
    print(f"❌ Error: {e}")
