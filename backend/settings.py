"""
Django settings for Claverica fintech backend.
Production-ready configuration for Render deployment.

Environment Variables Required:
- DJANGO_SECRET_KEY: Secret key for Django
- DATABASE_URL: PostgreSQL database URL
- DEBUG: Set to 'True' for development
- CORS_ALLOWED_ORIGINS: Comma-separated list of allowed origins

Optional:
- REDIS_URL: For caching and channels
- SENTRY_DSN: For error tracking
- EMAIL_*: For email configuration
- PUSHER_*: For real-time notifications
"""

# ============================================================================
# CRITICAL: Python Path Fix for Non-Standard Project Structure
# ============================================================================
import sys
import os
from pathlib import Path

# Fix Python path since manage.py is in parent directory
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

# Add backend directory to Python path (where your apps are)
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Add project directory to Python path
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# Print debug info (only in development)
if os.environ.get('DEBUG') == 'True':
    print(f"[OK] Python path configured")
    print(f"  Backend dir: {BACKEND_DIR}")
    print(f"  Project dir: {PROJECT_DIR}")
    print(f"  Current sys.path: {sys.path[:3]}...")
# ============================================================================

import warnings
from datetime import timedelta
from decimal import Decimal

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# ------------------------------
# TEST ENVIRONMENT DETECTION
# ------------------------------
def is_test_environment():
    """Check if we're running tests"""
    return ('test' in sys.argv or
            'pytest' in sys.modules or
            os.environ.get('DJANGO_TEST') == 'True' or
            os.environ.get('RUNNING_TESTS') == 'True')

# ------------------------------
# ENVIRONMENT VARIABLE HELPER
# ------------------------------
def get_env_variable(var_name, default=None, required=False):
    """Get environment variable or return default/raise error."""
    value = os.environ.get(var_name, default)
    if required and value is None:
        raise ImproperlyConfigured(f"Set the {var_name} environment variable")
    return value

# ------------------------------
# FRONTEND DOMAINS HELPER
# ------------------------------
def get_frontend_domains():
    """Get frontend domains from environment variable"""
    frontend_domains = get_env_variable('FRONTEND_DOMAINS', '')
    if frontend_domains:
        return [domain.strip() for domain in frontend_domains.split(',')]
    return []

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Warning: .env file not found at {env_path}")

# ------------------------------
# BASE DIRECTORY
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# SECRET KEY AND DEBUG
# ------------------------------
SECRET_KEY = get_env_variable(
    'DJANGO_SECRET_KEY',
    'django-insecure-CHANGE-THIS-IN-PRODUCTION',
    required=not (get_env_variable('DEBUG', 'False') == 'True')
)

# Set DEBUG based on environment
if is_test_environment():
    # Tests should run in development-like environment
    DEBUG = True
    print("[OK] Test environment detected, DEBUG set to True for testing")
else:
    DEBUG = get_env_variable('DEBUG', 'False') == 'True'

# Validate critical production variables
if not DEBUG and not is_test_environment():
    required_vars = ['DJANGO_SECRET_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ImproperlyConfigured(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

# ------------------------------
# API VERSION
# ------------------------------
API_VERSION = get_env_variable('API_VERSION', '1.0.0')
GIT_COMMIT = get_env_variable('RENDER_GIT_COMMIT', 'local')
APP_VERSION = f"{API_VERSION}-{GIT_COMMIT[:8]}" if GIT_COMMIT != 'local' else API_VERSION

# ============================================================================
# CRITICAL FIX: CUSTOM USER MODEL MUST BE DEFINED BEFORE INSTALLED_APPS
# ============================================================================
# This MUST be defined BEFORE INSTALLED_APPS to work properly
AUTH_USER_MODEL = 'accounts.Account'
print(f"[OK] AUTH_USER_MODEL set to: {AUTH_USER_MODEL}")
# ============================================================================

# ------------------------------
# ALLOWED HOSTS
# ------------------------------
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Add Render hostnames - ONLY claverica-backend-rniq.onrender.com
ALLOWED_HOSTS.append('claverica-backend-rniq.onrender.com')
ALLOWED_HOSTS.append('.claverica-backend-rniq.onrender.com')

# Remove this line to prevent duplicates from environment variable
# additional_hosts = get_env_variable('ALLOWED_HOSTS')
# if additional_hosts:
#     ALLOWED_HOSTS.extend([host.strip() for host in additional_hosts.split(',')])

# ------------------------------
# INSTALLED APPS - FIXED WITH backend. PREFIX
# ------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "backend.payments",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "django_extensions",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "backend.accounts",
    "backend.users",
    "backend.tasks",
    "backend.cards",
    "backend.crypto",
    "backend.escrow",
    "backend.notifications",
    "backend.kyc",
    "backend.compliance",
    "backend.tac",
    "backend.withdrawal",
    "backend.receipts",
    
    "backend.transactions",
    "backend.transfers"
    ]

# Add development tools (skip for tests) - ONLY drf_spectacular
if DEBUG and not is_test_environment():
    INSTALLED_APPS.append('drf_spectacular')

# ------------------------------
# MIDDLEWARE
# ------------------------------
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
]

# ------------------------------
# URLS AND TEMPLATES - FIXED URLs
# ------------------------------
ROOT_URLCONF = 'backend.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
WSGI_APPLICATION = 'backend.wsgi.application'

# Create template directory if it doesn't exist
template_dir = BASE_DIR / 'templates'
os.makedirs(template_dir, exist_ok=True)

# ------------------------------
# DATABASE - FIXED FOR RENDER POSTGRESQL & LOCAL SQLITE
# ------------------------------
# Always use SQLite for tests
if is_test_environment():
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("[OK] Using SQLite for testing")
else:
    # Check if we have a PostgreSQL database URL (for Render)
    database_url = get_env_variable('DATABASE_URL')

    if database_url and 'postgres' in database_url:
        # PostgreSQL for Render/Production
        try:
            DATABASES = {
                'default': dj_database_url.config(
                    default=database_url,
                    conn_max_age=600,
                    ssl_require=not DEBUG
                )
            }

            # Remove any sslmode parameter that might cause issues
            if 'OPTIONS' in DATABASES['default'] and 'sslmode' in DATABASES['default']['OPTIONS']:
                del DATABASES['default']['OPTIONS']['sslmode']

            if not DEBUG:
                DATABASES['default']['CONN_MAX_AGE'] = 600
                DATABASES['default']['CONN_HEALTH_CHECKS'] = True

            # Add PostgreSQL-specific optimizations
            DATABASES['default']['OPTIONS'] = {
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
            }
            print("[OK] Using PostgreSQL database (Render)")

            # DEBUG: Print database info for troubleshooting
            if DEBUG:
                print(f"  Database: {DATABASES['default']['NAME']}")
                print(f"  User: {DATABASES['default']['USER']}")
                print(f"  Host: {DATABASES['default']['HOST']}")
        except Exception as e:
            print(f"Error configuring PostgreSQL: {e}")
            print("Falling back to SQLite...")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
    else:
        # SQLite for local development
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
        print("[OK] Using SQLite for local development")

# ------------------------------
# PASSWORD HASHING
# ------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ------------------------------
# AUTHENTICATION BACKENDS
# ------------------------------
AUTHENTICATION_BACKENDS = [
    'backend.accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ------------------------------
# AUTH PASSWORD VALIDATORS
# ------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ------------------------------
# INTERNATIONALIZATION
# ------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------------
# STATIC AND MEDIA FILES - FIXED FOR WHITENOISE
# ------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Add this line for static file directories
STATICFILES_DIRS = [BASE_DIR / "static"]  # For development static files

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Create media directories if they don't exist
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(MEDIA_ROOT / 'receipts', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'profiles', exist_ok=True)

# Create static directory if it doesn't exist
static_dir = BASE_DIR / "static"
os.makedirs(static_dir, exist_ok=True)

# ------------------------------
# WHITENOISE SETTINGS
# ------------------------------
WHITENOISE_AUTOREFRESH = DEBUG  # Auto-refresh static files in development
WHITENOISE_MAX_AGE = 31536000  # Cache static files for 1 year in production
WHITENOISE_USE_FINDERS = True  # Use Django's staticfiles finders
WHITENOISE_ROOT = None  # Don't serve files from root
WHITENOISE_MANIFEST_STRICT = not DEBUG  # Strict manifest checking in production

# ------------------------------
# DEFAULT AUTO FIELD
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------
# REST FRAMEWORK - UPDATED THROTTLE SETTINGS
# ------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '30/minute',
        'transaction': '60/minute',
        'transfer': '60/minute',
        'auth': '1000/minute'  # Increased to avoid throttling during testing,
    },
}

# Add API documentation for development (skip for tests)
if DEBUG and not is_test_environment():
    REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

# ------------------------------
# SIMPLE JWT CONFIGURATION
# ------------------------------
SIMPLE_JWT = {
    # DISABLED - Using middleware override
}

# ------------------------------
# CORS - UPDATED FOR REACT FRONTEND
# ------------------------------
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Base development origins
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
    'https://claverica-backend-rniq.onrender.com',
]

# Add ONLY your Render domain

# Get frontend domains from environment
frontend_domains = get_frontend_domains()
if frontend_domains:
    CORS_ALLOWED_ORIGINS.extend(frontend_domains)
    print(f"[OK] Frontend domains added to CORS: {frontend_domains}")

# For production, ensure we don't allow all origins
if not DEBUG and not is_test_environment():
    # Disable CORS_ALLOW_ALL_ORIGINS in production
    CORS_ALLOW_ALL_ORIGINS = False

    # Fallback to environment variable if no frontend domains set
    if not CORS_ALLOWED_ORIGINS:
        cors_origins = get_env_variable(
            'CORS_ALLOWED_ORIGINS',
            'http://localhost:3000,http://localhost:5173'
        )
        if cors_origins:
            CORS_ALLOWED_ORIGINS = [
    'origin.strip() for origin in cors_origins.split(",")',
]
            print(f"[OK] CORS origins from env: {CORS_ALLOWED_ORIGINS}")

# Session cookie settings for HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# For development, you can disable these (but not recommended for production)
# CSRF_COOKIE_SECURE = False
# SESSION_COOKIE_SECURE = False

# DISABLE ALL AUTHENTICATION FOR MOCK MODE
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

# DISABLE ALL AUTHENTICATION FOR MOCK MODE
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}
########################################
# DEPLOYED: Fri Jan 23 02:00:04 UTC 2026
# Mock auth enabled for test@claverica.com
########################################

########################################
# VISIBLE DEPLOYMENT: Fri Jan 23 02:01:29 UTC 2026
# Mock authentication enabled
# Test: test@claverica.com / Test@123
########################################
