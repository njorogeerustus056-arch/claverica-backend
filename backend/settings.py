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
        print(f"[OK] Local: Loaded .env file from {env_path}")
    else:
        print("[WARN] Local: No .env file found at", env_path)
else:
    print("[OK] Railway: Using environment variables")

# ==============================================================================
# APP CONFIGURATION
# ==============================================================================
APP_NAME = 'Claverica'
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://claverica-fixed.vercel.app')

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
        print("[WARN] WARNING: Using development SECRET_KEY - DO NOT USE IN PRODUCTION")

# ==============================================================================
# DEBUG & HOSTS SETTINGS - FIXED: Added localhost for testing
# ==============================================================================
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

if os.environ.get('RAILWAY') or os.environ.get('RAILWAY_ENVIRONMENT'):
    ALLOWED_HOSTS = ['*', '.up.railway.app']
    CSRF_TRUSTED_ORIGINS = [
        'https://*.railway.app',
        'https://claverica-fixed.vercel.app',
        'https://claverica-frontend-vercel.vercel.app',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173',
    ]
    print(f"[OK] Railway: ALLOWED_HOSTS = {ALLOWED_HOSTS}")
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
    'sendgrid_backend',
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
# MIDDLEWARE
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
# TEMPLATES CONFIGURATION - FIXED: Removed duplicate entry
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'accounts/templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': False,
        },
    },
]

print(f"[OK] Template directories: {TEMPLATES[0]['DIRS']}")
print(f"[OK] BASE_DIR: {BASE_DIR}")

WSGI_APPLICATION = 'backend.wsgi.application'

# ==============================================================================
# DATABASE - PostgreSQL for Railway, SQLite for local
# ==============================================================================
import dj_database_url

# Check if we're on Railway
IS_RAILWAY = os.environ.get('RAILWAY') or os.environ.get('RAILWAY_ENVIRONMENT')

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if IS_RAILWAY and not DATABASE_URL:
    print("[ERROR] RAILWAY: DATABASE_URL not set in Railway environment!")
    print("[ERROR] Please set DATABASE_URL in Railway Dashboard > Variables")

if DATABASE_URL:
    # Parse database URL
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
            ssl_require=True if IS_RAILWAY else False
        )
    }

    # Add PostgreSQL-specific options only for PostgreSQL
    if 'postgres' in DATABASE_URL:
        DATABASES['default']['OPTIONS'] = {
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        }
        print("[OK] Using PostgreSQL database with optimized settings")
    else:
        print("[OK] Using database from URL")
else:
    # Local development with SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("[WARN] Local development: Using SQLite database - not for production")

# ==============================================================================
# REST FRAMEWORK & JWT
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
        'login': '5/15min',
    }
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ==============================================================================
# STATIC FILES
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if os.path.exists(BASE_DIR / 'static') else []

# ==============================================================================
# CORS SETTINGS - FIXED: Added localhost for testing
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'https://claverica-fixed.vercel.app',
        'https://claverica-frontend-vercel.vercel.app',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5173',
    ]
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# EMAIL CONFIGURATION - SENDGRID FOR RAILWAY
# ==============================================================================
if DEBUG:
    # Development: use console for testing
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("[OK] Development: Using console email backend")
else:
    # Production on Railway: Use SendGrid HTTP API
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

    # SendGrid specific settings
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False
    SENDGRID_TRACK_EMAIL_OPENS = True
    SENDGRID_TRACK_CLICKS_PLAIN = True

    if not SENDGRID_API_KEY:
        print("[WARN] WARNING: SENDGRID_API_KEY not set in environment variables")
    else:
        print("[OK] Production: Using SendGrid HTTP API")

# This is what clients will see - using your verified sender!
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Claverica <noreply@claverica.com>')

print(f"[OK] DEFAULT FROM: {DEFAULT_FROM_EMAIL}")
print(f"[OK] FRONTEND URL: {FRONTEND_URL}")
print(f"[OK] APP NAME: {APP_NAME}")

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
# CACHE CONFIGURATION - UPDATED with Redis support
# ==============================================================================
if os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
        }
    }
    print("[OK] Using Redis cache")
    
    # Use Redis for session storage (better performance)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    print("[OK] Using in-memory cache (ok for development)")

# ==============================================================================
# PUSHER CONFIGURATION FOR REAL-TIME NOTIFICATIONS
# ==============================================================================
PUSHER_APP_ID = os.environ.get('PUSHER_APP_ID', '2116646')
PUSHER_KEY = os.environ.get('PUSHER_KEY', 'b1283987f8301fdc6e34')
PUSHER_SECRET = os.environ.get('PUSHER_SECRET', 'cf8356970f233d885c49')
PUSHER_CLUSTER = os.environ.get('PUSHER_CLUSTER', 'us3')
PUSHER_SSL = True

print(f"[OK] Pusher configured with cluster: {PUSHER_CLUSTER}")

# ==============================================================================
# PRINT CONFIG STATUS
# ==============================================================================
print(f"[OK] DEBUG: {DEBUG}")
print(f"[OK] SECRET_KEY set: {'YES' if SECRET_KEY else 'NO'}")
print(f"[OK] RAILWAY environment: {'YES' if IS_RAILWAY else 'NO'}")
print(f"[OK] DATABASE: {'PostgreSQL' if DATABASE_URL and 'postgres' in DATABASE_URL else 'SQLite'}")
print(f"[OK] Database CONN_MAX_AGE: {DATABASES['default'].get('CONN_MAX_AGE', 'Not set')}")

# ==============================================================================
# DATABASE DEBUGGING
# ==============================================================================
print(f"[OK] RAW DATABASE_URL from env: {os.environ.get('DATABASE_URL', 'NOT SET')}")

# Force the correct host if needed
if DATABASE_URL and 'postgres.railway.internal' in DATABASE_URL:
    corrected_url = DATABASE_URL.replace('postgres.railway.internal', 'postgres-aaoa.railway.internal')
    print(f"[OK] CORRECTED DATABASE_URL from: {DATABASE_URL} to: {corrected_url}")
    os.environ['DATABASE_URL'] = corrected_url