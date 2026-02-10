"""
WSGI config for backend project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)  # Goes up one level from backend/
sys.path.insert(0, project_dir)      # Add D:\Erustus\claverica-backend
sys.path.insert(0, current_dir)      # Add D:\Erustus\claverica-backend\backend

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_wsgi_application()
