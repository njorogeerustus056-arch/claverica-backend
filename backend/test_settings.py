# test_settings.py - ADD DEBUG_TOOLBAR TO INSTALLED_APPS
"""
Test-specific settings that exclude optional packages.
"""
import os
from pathlib import Path
import sys

# Add the project to path
project_path = Path(__file__).resolve().parent
sys.path.insert(0, str(project_path))

# Load original settings but modify it
from backend.settings import *

# ====================================================
# TEST-SPECIFIC OVERRIDES
# ====================================================

# Force DEBUG=True for tests to disable production security
DEBUG = True

# Disable all security redirects for tests
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_REFERRER_POLICY = None

# Allow HTTP for tests
SECURE_PROXY_SSL_HEADER = None

# Remove health_check from INSTALLED_APPS for testing
# But KEEP debug_toolbar if it was in original settings
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in [
    'health_check',
    'health_check.db', 
    'health_check.cache',
    'health_check.storage',
    'django_extensions',  # Optional for tests
]]

# If debug_toolbar was in INSTALLED_APPS, add it back
if 'debug_toolbar' in INSTALLED_APPS:
    # It's already there, keep it
    pass
else:
    # Check if we should add it for development
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        print("✅ Added debug_toolbar to INSTALLED_APPS")
    except ImportError:
        print("⚠ debug_toolbar not installed")

# Use simpler channel layers for tests
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Disable Pusher for tests
PUSHER_APP_ID = None
PUSHER_KEY = None
PUSHER_SECRET = None
PUSHER_CLUSTER = None

# Use SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for tests
    }
}

# Disable email sending during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Simpler REST framework settings for tests
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}

# Disable logging during tests
import logging
logging.disable(logging.CRITICAL)

# Ensure test environment is detected
os.environ['DJANGO_TEST'] = 'True'
os.environ['RUNNING_TESTS'] = 'True'

print("✅ Test settings loaded (DEBUG=True, security disabled, SQLite in-memory DB)")