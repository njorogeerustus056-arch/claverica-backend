"""
WSGI config for Claverica backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Get the WSGI application
application = get_wsgi_application()

# Wrap with WhiteNoise for static files
application = WhiteNoise(application, root=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles'))