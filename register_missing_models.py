import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.contrib import admin

print("📝 REGISTERING MISSING MODELS IN ADMIN:")

# List of apps that might have unregistered models
apps_to_check = ['kyc', 'crypto', 'escrow', 'claverica_tasks', 'compliance', 'tac', 'withdrawal', 'receipts', 'tasks']

for app_name in apps_to_check:
    try:
        # Get the app config
        app_config = django.apps.apps.get_app_config(app_name)
        models = list(app_config.get_models())
        
        print(f"\n🔍 {app_name}: {len(models)} models")
        
        # Check which are registered
        for model in models:
            is_registered = model in admin.site._registry
            status = "✅" if is_registered else "❌"
            print(f"   {status} {model.__name__}")
            
    except Exception as e:
        print(f"\n⚠️  {app_name}: {str(e)[:50]}")

print(f"\n📊 Total registered: {len(admin.site._registry)} models")
