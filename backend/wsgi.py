"""
WSGI config for backend project.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# Add paths explicitly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()
application = WhiteNoise(application)  # ✅ Add this line