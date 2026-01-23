import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.apps import apps

print("=== BACKEND APPS STATUS ===")
backend_apps = []

for config in apps.app_configs.values():
    if config.name.startswith('backend.'):
        backend_apps.append(config.name)

print(f"🎯 Found {len(backend_apps)} backend apps:")

for app in sorted(backend_apps):
    try:
        config = apps.get_app_config(app.split('.')[1])
        models = list(config.get_models())
        status = '✅' if models else '⚠️ '
        print(f"{status} {app}: {len(models)} models")
    except Exception as e:
        print(f"❌ {app}: Error - {str(e)[:50]}")

print(f"\n📊 TOTAL: {len(backend_apps)} backend apps loaded")
