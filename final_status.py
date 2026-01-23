import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    import django
    django.setup()
    from django.apps import apps
    
    print("=== FINAL CLAVERICA STATUS ===")
    
    backend_apps = []
    working = 0
    total_models = 0
    
    for config in apps.app_configs.values():
        if config.name.startswith('backend.'):
            backend_apps.append(config.name)
            try:
                models = list(config.get_models())
                if models:
                    working += 1
                    total_models += len(models)
                    print(f"✅ {config.name}: {len(models)} models")
                else:
                    print(f"⚠️  {config.name}: No models")
            except:
                print(f"❌ {config.name}: Error")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Backend apps: {len(backend_apps)}")
    print(f"  Working apps: {working}/{len(backend_apps)}")
    print(f"  Total models: {total_models}")
    
    if working == len(backend_apps):
        print("\n🎉🎉🎉 ALL APPS WORKING! CLAVERICA READY! 🎉🎉🎉")
    else:
        print(f"\n⚠️  {len(backend_apps) - working} apps need attention")
        
except Exception as e:
    print(f"❌ Django setup failed: {e}")
