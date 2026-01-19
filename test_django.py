import sys
import os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    # First try to import django without setup to check settings
    import django
    print('✅ Django imported')
    
    # Check settings
    from django.conf import settings
    
    # Check if our apps are in INSTALLED_APPS
    receipt_apps = [app for app in settings.INSTALLED_APPS if 'receipt' in app]
    print(f'Receipt apps in settings: {receipt_apps}')
    
    # Try setup
    django.setup()
    print('✅ Django setup successful!')
    
except Exception as e:
    print(f'❌ Error: {e}')
    
    # Get more details
    import traceback
    tb = traceback.format_exc()
    
    # Look for the specific error line
    for line in tb.split('\n'):
        if 'ModuleNotFoundError' in line or 'receipt' in line.lower():
            print(f'Error details: {line}')
