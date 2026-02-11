"""
WSGI config for backend project - with automatic path fixing
"""
import os
import sys

# THIS IS THE CRITICAL FIX - Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Add both directories to Python path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"✅ Added parent_dir to path: {parent_dir}")

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"✅ Added current_dir to path: {current_dir}")

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("✅ Django WSGI application loaded successfully")
except Exception as e:
    print(f"❌ Failed to load Django WSGI application: {e}")
    import traceback
    traceback.print_exc()
    
    # Fallback that returns error details
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        error_msg = f"Django failed to start: {e}\n\nPython path: {sys.path}\nCurrent dir: {os.getcwd()}"
        return [error_msg.encode('utf-8')]
