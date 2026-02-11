"""
ULTRA MINIMAL Django settings for Railway health check
NO IMPORTS from other settings files
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CRITICAL - MUST BE SET
SECRET_KEY = 'django-insecure-health-check-only'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ABSOLUTELY CRITICAL - DISABLE ALL REDIRECTS
APPEND_SLASH = False
PREPEND_WWW = False

# Minimal apps
INSTALLED_APPS = []

# Minimal middleware - NO redirect middleware
MIDDLEWARE = []

ROOT_URLCONF = 'backend.urls_health'  # Use a SEPARATE url config

# Simple SQLite database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

# No auth needed
AUTH_USER_MODEL = 'accounts.Account'  # Keep this for compatibility

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_TZ = False

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# FORCE NO REDIRECTS AGAIN AT THE END
APPEND_SLASH = False
