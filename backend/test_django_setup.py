import os
import sys

# Simulate Railway environment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

print("=== Django Setup Test ===")
print(f"Current dir: {current_dir}")
print(f"Project root: {project_root}")

# Add to path like Railway will
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"\nPython path:")
for i, path in enumerate(sys.path[:5]):
    print(f"  {i+1}. {path}")

try:
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    
    import django
    django.setup()
    print("\n Django setup successful!")
    
    # Test settings
    from django.conf import settings
    print(f" Settings loaded: DEBUG={settings.DEBUG}")
    print(f" ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f" DATABASES configured: {'default' in settings.DATABASES}")
    
    # Test the health endpoint from urls.py
    from django.test import RequestFactory
    import backend.urls
    import importlib
    importlib.reload(backend.urls)
    
    # Find the railway_health function
    if hasattr(backend.urls, 'railway_health'):
        factory = RequestFactory()
        request = factory.get('/')
        response = backend.urls.railway_health(request)
        print(f" Health endpoint works: {response.status_code}")
    else:
        print(" railway_health function not found in urls.py")
        
except Exception as e:
    print(f"\n Error: {e}")
    import traceback
    traceback.print_exc()
