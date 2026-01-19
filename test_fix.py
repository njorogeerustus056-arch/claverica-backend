import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
try:
    import django
    django.setup()
    print("✅ Django loaded!")
except Exception as e:
    print(f"❌ Error: {str(e)[:100]}")
