"""
WSGI config - using ULTRA MINIMAL settings for Railway health check
"""
import os
import sys

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Use the COMPLETELY STANDALONE minimal settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings_railway_minimal')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
print("✅ WSGI loaded with ULTRA MINIMAL settings - NO REDIRECTS")
