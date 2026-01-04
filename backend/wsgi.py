"""
WSGI config for Claverica backend project.
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()

# Get absolute path for Render
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Debug output
print(f"WhiteNoise initialization:")
print(f"  STATIC_ROOT: {STATIC_ROOT}")
print(f"  Directory exists: {STATIC_ROOT.exists()}")

application = WhiteNoise(application, root=str(STATIC_ROOT))
application.add_files(str(STATIC_ROOT), prefix='/static/')