import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.conf import settings

# Get the settings module
import backend.settings as settings_module

# 1. Remove ALL authentication from REST_FRAMEWORK
settings_module.REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],  # EMPTY - NO AUTH
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'UNAUTHENTICATED_USER': None,  # Important: no user object
    'UNAUTHENTICATED_TOKEN': None,
}

# 2. Remove SimpleJWT from INSTALLED_APPS
if 'rest_framework_simplejwt' in settings_module.INSTALLED_APPS:
    settings_module.INSTALLED_APPS.remove('rest_framework_simplejwt')

# 3. Empty SIMPLE_JWT settings
settings_module.SIMPLE_JWT = {}

# 4. Add a middleware that disables auth
settings_module.MIDDLEWARE = [
    'backend.middleware.force_auth.ForceAuthMiddleware',
] + [mw for mw in settings_module.MIDDLEWARE 
     if 'auth' not in mw.lower() and 'AuthenticationMiddleware' not in mw]

print("✅ NUCLEAR AUTH DISABLED")
print("✅ No authentication classes")
print("✅ SimpleJWT removed from INSTALLED_APPS")
print("✅ Auth middleware removed")
