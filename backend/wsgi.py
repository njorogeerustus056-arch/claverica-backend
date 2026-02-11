"""
WSGI config - using minimal settings for Railway health check
"""
import os
import sys

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use minimal settings for Railway
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_railway')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
print("✅ WSGI loaded with minimal settings for Railway health check")
