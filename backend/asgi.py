"""
ASGI config for Claverica backend project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Use standard ASGI application (no channels)
application = get_asgi_application()