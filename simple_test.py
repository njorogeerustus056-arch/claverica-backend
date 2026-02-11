# simple_test.py - Test if Django can be imported correctly
import os
import sys

print("Current directory:", os.getcwd())
print("Python path:", sys.path)

try:
    # Try to import the backend module
    import backend
    print("? backend module imported")
    print("backend location:", backend.__file__)
    
    # Try to import settings
    import backend.settings
    print("? settings imported")
    
    # Try to get Django setup
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    import django
    django.setup()
    print("? Django setup complete")
    
    # Try to get wsgi application
    from backend.wsgi import application
    print("? WSGI application loaded")
    
except Exception as e:
    print(f"? Error: {e}")
    import traceback
    traceback.print_exc()
