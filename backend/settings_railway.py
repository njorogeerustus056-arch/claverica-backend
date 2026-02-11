"""
Minimal settings for Railway health check
"""
import os
from .settings import *

# Override with minimal middleware for health check
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# Ensure root URL works
ROOT_URLCONF = 'backend.urls'

# Disable any authentication requirements for health check
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

# Make sure health check doesn't require database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

# Debug settings
DEBUG = True
ALLOWED_HOSTS = ['*']
