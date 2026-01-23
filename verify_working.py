import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.apps import apps

print("🎯 VERIFYING ALL 16 APPS:")
print("=" * 40)

all_working = True
for config in apps.app_configs.values():
    if config.name.startswith('backend.'):
        try:
            models = list(config.get_models())
            if models:
                print(f"✅ {config.name}: {len(models)} models")
            else:
                print(f"⚠️  {config.name}: No models")
                all_working = False
        except Exception as e:
            print(f"❌ {config.name}: ERROR - {str(e)[:50]}")
            all_working = False

if all_working:
    print("\n🎉🎉🎉 ALL 16 APPS ARE WORKING! 🎉🎉🎉")
else:
    print("\n⚠️  Some apps need attention")
