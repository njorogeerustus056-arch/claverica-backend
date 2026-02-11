\"\"\"
WSGI config - FORCED to use main settings with APPEND_SLASH=False
\"\"\"
import os
import sys

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# FORCE the main settings with redirects disabled
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings_railway'
os.environ['APPEND_SLASH'] = 'False'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
print("🚀 WSGI loaded with FORCED settings - NO REDIRECTS")
