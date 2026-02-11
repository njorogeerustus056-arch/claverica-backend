"""
Django settings for Claverica backend project
Production-ready configuration for Railway deployment
"""

import os
import sys
from pathlib import Path
from datetime import timedelta

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
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
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

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # THIS ENABLES collectstatic
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'channels',
    'django_extensions',
    
    # Your apps
    'accounts',
    'cards',
    'compliance',
    'kyc',
    'kyc_spec',
    'notifications',
    'notifications_backup',
    'payments',
    'receipts',
    'tasks',
    'transactions',
    'transfers',
    'users',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI Application
WSGI_APPLICATION = 'backend.wsgi.application'

# ==============================================================================
# DATABASE
# ==============================================================================

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
else:
    # Local development with SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==============================================================================
# REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# ==============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# ==============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# CHANNELS (ASGI) CONFIGURATION
# ==============================================================================

ASGI_APPLICATION = 'backend.asgi.application'

# ==============================================================================
# CORS SETTINGS
# ==============================================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all in development
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'https://claverica-fixed.vercel.app',
        'https://claverica-frontend-vercel.vercel.app',
    ]

CORS_ALLOW_CREDENTIALS = True

