"""
Django settings for Claverica backend project
Production-ready configuration for Railway deployment
"""

import os
import sys
from pathlib import Path

# ==============================================================================
# CRITICAL: PYTHON PATH SETUP
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv()

from datetime import timedelta




# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-development-key-change-in-production'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# SIMPLE FIX: ALLOW ALL HOSTS IN RAILWAY, RESTRICTED IN DEVELOPMENT
if os.environ.get('RAILWAY') or os.environ.get('RAILWAY_ENVIRONMENT'):
    ALLOWED_HOSTS = ['*', '.up.railway.app', 'claverica-backend-production.up.railway.app']
    print("🚀 Railway: ALLOWED_HOSTS set to '*' for health checks")
else:
    # CSRF and Security Settings
    CSRF_TRUSTED_ORIGINS = [
        'https://*.railway.app',
        'https://claverica-fixed.vercel.app',
        'https://claverica-frontend-vercel.vercel.app',
        'http://localhost:3000',
        'http://localhost:5173',
    ]

# Security settings for production only
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# [REST OF YOUR SETTINGS - KEEP EVERYTHING ELSE AS IS]


# WSGI Application
WSGI_APPLICATION = 'backend.wsgi.application'




# Railway Database Configuration
import dj_database_url

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
