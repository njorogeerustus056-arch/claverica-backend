"""
Django settings for Claverica backend project
Production-ready configuration for Railway deployment
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# ==============================================================================
# CRITICAL: PYTHON PATH SETUP
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env ONLY in development, NEVER in Railway
if not os.environ.get('RAILWAY'):
    # FIXED: Look in backend folder, not parent directory
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"??? Local: Loaded .env file from {env_path}")
    else:
        print("??? Local: No .env file found at", env_path)
else:
    print("??? Railway: Using environment variables")

# ==============================================================================
# CRITICAL: SECRET_KEY MUST BE SET IN RAILWAY
# ==============================================================================
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    if os.environ.get('RAILWAY'):
        raise ValueError(
            "CRITICAL: SECRET_KEY environment variable is not set in Railway. "
            "Please add it in Railway Dashboard > Variables."
        )
    else:
        SECRET_KEY = 'django-insecure-development-key-change-in-production'
        print("??  WARNING: Using development SECRET_KEY - DO NOT USE IN PRODUCTION")

# ==============================================================================
# DEBUG & HOSTS SETTINGS
# ==============================================================================
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

if os.environ.get('RAILWAY') or os.environ.get('RAILWAY_ENVIRONMENT'):
    ALLOWED_HOSTS = ['*', '.up.railway.app']
    CSRF_TRUSTED_ORIGINS = [
        'https://*.railway.app',
        'https://claverica-fixed.vercel.app',
        'https://claverica-frontend-vercel.vercel.app',
    ]
    print(f"??? Railway: ALLOWED_HOSTS = {ALLOWED_HOSTS}")
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5173',
    ]

# ==============================================================================
# SECURITY SETTINGS - PRODUCTION ONLY
# ==============================================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    # Exempt health check from SSL redirect
    SECURE_REDIRECT_EXEMPT = [r'^health/?$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
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
    'django.contrib.staticfiles',

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
    'payments',
    'receipts',
    'tasks',
    'transactions',
    'transfers',
    'users',
]

# ==============================================================================
# MIDDLEWARE - ADDED DATABASE CONNECTION MIDDLEWARE TO PREVENT TIMEOUTS
# ==============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'backend.db_utils.DatabaseConnectionMiddleware',  # Added to prevent connection leaks
]

ROOT_URLCONF = 'backend.urls'

# ==============================================================================
# TEMPLATES CONFIGURATION - FIXED FOR EMAIL TEMPLATES
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Add explicit template directories to ensure email templates are found
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'accounts/templates'),
            str(BASE_DIR / 'accounts' / 'templates'),
        ],
        'APP_DIRS': True,  # This will also find templates in app directories
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': False,  # Disable template debug in production for performance
        },
    },
]

# Add debug to see what paths are being used (visible in Railway logs)
print(f"??? Template directories: {TEMPLATES[0]['DIRS']}")
print(f"??? BASE_DIR: {BASE_DIR}")

WSGI_APPLICATION = 'backend.wsgi.application'

# ==============================================================================
# DATABASE - RAILWAY POSTGRESQL - FIXED CONNECTION HANDLING
# ==============================================================================
import dj_database_url

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,  # Reduced from 600 to 60 seconds to prevent connection leaks
            conn_health_checks=True,
            ssl_require=True if os.environ.get('RAILWAY') else False
        )
    }

    # Add these connection settings to prevent timeouts
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5,
    }

    print(f"??? Using PostgreSQL database with optimized settings")
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("??  Using SQLite database - not for production")

# ==============================================================================
# REST FRAMEWORK & JWT - WITH RATE LIMITING
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'login': '5/15min',  # 5 attempts per 15 minutes for login
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ==============================================================================
# STATIC FILES - WHITENOISE
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if os.path.exists(BASE_DIR / 'static') else []

# ==============================================================================
# CORS SETTINGS
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'https://claverica-fixed.vercel.app',
        'https://claverica-frontend-vercel.vercel.app',
    ]
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# EMAIL CONFIGURATION - COMPLETE FIX FOR BOTH PORTS
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))  # Railway should override this

# Print what port we're using
print(f"??? EMAIL PORT from env: {os.environ.get('EMAIL_PORT')}")
print(f"??? EMAIL PORT being used: {EMAIL_PORT}")

# Set SSL/TLS based on port number
if EMAIL_PORT == 465:
    # Port 465 uses SSL
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
    print("??? Using SSL for port 465")
elif EMAIL_PORT == 587:
    # Port 587 uses TLS
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = True
    print("??? Using TLS for port 587")
else:
    # For any other port, read from environment
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    print(f"??? Using env vars - SSL: {EMAIL_USE_SSL}, TLS: {EMAIL_USE_TLS}")

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Claverica <noreply@claverica.com>')

# Print final settings
print(f"??? EMAIL HOST: {EMAIL_HOST}")
print(f"??? EMAIL PORT: {EMAIL_PORT}")
print(f"??? EMAIL USE SSL: {EMAIL_USE_SSL}")
print(f"??? EMAIL USE TLS: {EMAIL_USE_TLS}")

# ==============================================================================
# AUTHENTICATION
# ==============================================================================
AUTH_USER_MODEL = 'accounts.Account'

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
# CACHE CONFIGURATION - FOR RATE LIMITING
# ==============================================================================
# Use in-memory cache for development, Railway will use default
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# For production on Railway, you can use Redis later
if os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
        }
    }
    print("??? Using Redis cache")
else:
    print("??? Using in-memory cache (ok for development)")

# ==============================================================================
# DATABASE CONNECTION MANAGEMENT - PREVENT TIMEOUTS
# ==============================================================================
# Close database connections after each request to prevent connection leaks
# This is already set above with conn_max_age=60

# ==============================================================================
# PRINT CONFIG STATUS (Visible in Railway logs)
# ==============================================================================
print(f"??? DEBUG: {DEBUG}")
print(f"??? SECRET_KEY set: {'YES' if SECRET_KEY else 'NO'}")
print(f"??? RAILWAY environment: {'YES' if os.environ.get('RAILWAY') else 'NO'}")
print(f"??? DATABASE: {'PostgreSQL' if DATABASE_URL else 'SQLite'}")
print(f"??? Database CONN_MAX_AGE: {DATABASES['default'].get('CONN_MAX_AGE', 'Not set')}")

# ==============================================================================
# DATABASE DEBUGGING - ADD THIS TEMPORARILY
# ==============================================================================
import os
print(f"??? RAW DATABASE_URL from env: {os.environ.get('DATABASE_URL', 'NOT SET')}")

# Force the correct host if needed
if os.environ.get('DATABASE_URL'):
    db_url = os.environ.get('DATABASE_URL')
    if 'postgres.railway.internal' in db_url:
        corrected_url = db_url.replace('postgres.railway.internal', 'postgres-aaoa.railway.internal')
        print(f"??? CORRECTED DATABASE_URL from: {db_url} to: {corrected_url}")
        os.environ['DATABASE_URL'] = corrected_url