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
    print(f"✓ Python path configured")
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
    print("✓ Test environment detected, DEBUG set to True for testing")
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
print(f"✓ AUTH_USER_MODEL set to: {AUTH_USER_MODEL}")
# ============================================================================

# ------------------------------
# ALLOWED HOSTS
# ------------------------------
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Add Render hostnames
ALLOWED_HOSTS.append('claverica-backend-rniq.onrender.com')
ALLOWED_HOSTS.append('.claverica-backend-rniq.onrender.com')
ALLOWED_HOSTS.append('claverica-backend.onrender.com')
ALLOWED_HOSTS.append('.claverica-backend.onrender.com')

# Add any additional allowed hosts from environment
additional_hosts = get_env_variable('ALLOWED_HOSTS')
if additional_hosts:
    ALLOWED_HOSTS.extend([host.strip() for host in additional_hosts.split(',')])

# ------------------------------
# INSTALLED APPS - FIXED ORDER FOR CUSTOM USER MODEL
# ------------------------------
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    # Static files
    'django.contrib.staticfiles',
    
    # Health checks
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    
    # Third-party apps
    'django_extensions',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
    # ============================================
    # YOUR CUSTOM APPS - ACCOUNTS MUST BE FIRST!
    # ============================================
    'accounts',  # ← CRITICAL: Must be before any other custom app
    
    # Other custom apps (order matters for dependencies)
    'users',
    'tasks',
    'cards',
    'compliance',
    'crypto',
    'escrow',
    'notifications',
    'payments',
    'receipts',
    'transactions',
    'transfers',
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
    print("✓ Using SQLite for testing")
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
            print("✓ Using PostgreSQL database (Render)")
            
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
        print("✓ Using SQLite for local development")

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
    'accounts.backends.EmailBackend',
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
        'anon': '100/hour',        # CHANGED: Increased from 100/day to 100/hour
        'user': '1000/hour',       # CHANGED: Increased from 1000/day to 1000/hour
        'login': '30/minute',      # CHANGED: Increased from 10/minute to 30/minute
        'transaction': '60/minute', # CHANGED: Increased from 30/minute to 60/minute
        'transfer': '60/minute',    # CHANGED: Increased from 20/minute to 60/minute
        'auth': '30/minute',       # ADDED: For token refresh/verification endpoints
    },
}

# Add API documentation for development (skip for tests)
if DEBUG and not is_test_environment():
    REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'

# ------------------------------
# SIMPLE JWT CONFIGURATION
# ------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULES': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
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
]

# Add Render domains
CORS_ALLOWED_ORIGINS.append('https://claverica-backend-rniq.onrender.com')
CORS_ALLOWED_ORIGINS.append('https://claverica-backend.onrender.com')

# Get frontend domains from environment
frontend_domains = get_frontend_domains()
if frontend_domains:
    CORS_ALLOWED_ORIGINS.extend(frontend_domains)
    print(f"✓ Frontend domains added to CORS: {frontend_domains}")

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
            CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',')]
            print(f"✓ CORS origins from env: {CORS_ALLOWED_ORIGINS}")

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'content-disposition',
    'x-csrf-token',
]

# ------------------------------
# SECURITY
# ------------------------------
if not DEBUG and not is_test_environment():
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # In development/test, disable HTTPS redirects
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0  # Disable HSTS in development

# ------------------------------
# CSRF TRUSTED ORIGINS - UPDATED FOR REACT
# ------------------------------
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]

# Add Render domains to CSRF
CSRF_TRUSTED_ORIGINS.append('https://claverica-backend-rniq.onrender.com')
CSRF_TRUSTED_ORIGINS.append('https://claverica-backend.onrender.com')

# Add frontend domains to CSRF
for domain in frontend_domains:
    if domain not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(domain)

# Add CSRF origins from environment
csrf_origins = get_env_variable('CSRF_TRUSTED_ORIGINS')
if csrf_origins:
    for origin in csrf_origins.split(','):
        origin = origin.strip()
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

# Session security
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax' if DEBUG else 'Strict'
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = False

# ------------------------------
# RECEIPT SETTINGS
# ------------------------------
RECEIPT_STORAGE_PATH = MEDIA_ROOT / 'receipts'
ALLOWED_RECEIPT_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'image/webp',
]
MAX_RECEIPT_SIZE = 10 * 1024 * 1024

# ------------------------------
# FINTECH SETTINGS
# ------------------------------
TRANSACTION_LIMITS = {
    'daily_limit': Decimal('10000.00'),
    'single_transaction_limit': Decimal('5000.00'),
    'monthly_limit': Decimal('50000.00'),
}
KYC_VERIFICATION_REQUIRED = True
COMPLIANCE_CHECK_ENABLED = True

# ------------------------------
# HEALTH CHECK SETTINGS
# ------------------------------
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,    # in MB
}

# ------------------------------
# Suppress DRF min_value warning
# ------------------------------
warnings.filterwarnings("ignore", category=UserWarning, module="rest_framework.fields")

# ------------------------------
# PUSHER CONFIG
# ------------------------------
PUSHER_APP_ID = get_env_variable("PUSHER_APP_ID")
PUSHER_KEY = get_env_variable("PUSHER_KEY")
PUSHER_SECRET = get_env_variable("PUSHER_SECRET")
PUSHER_CLUSTER = get_env_variable("PUSHER_CLUSTER")
if not all([PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER]):
    print("Warning: Pusher env vars are missing")
else:
    print("Success: Pusher env vars loaded successfully")

# ------------------------------
# CACHE CONFIGURATION
# ------------------------------
redis_url = get_env_variable('REDIS_URL')
if not DEBUG and redis_url and not is_test_environment():
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": redis_url,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                # IMPORTANT: Configure Redis for throttling
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "RETRY_ON_TIMEOUT": True,
                "MAX_CONNECTIONS": 1000,
            }
        }
    }
    
    # Configure DRF to use Redis for throttling
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
        'rest_framework.throttling.ScopedRateThrottle',
    ]
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# ------------------------------
# ERROR MONITORING (Sentry)
# ------------------------------
sentry_dsn = get_env_variable('SENTRY_DSN')
if not DEBUG and sentry_dsn and not is_test_environment():
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment="production" if not DEBUG else "development",
            release=APP_VERSION,
        )
        print("Success: Sentry initialized successfully")
    except ImportError:
        print("Warning: Sentry SDK not installed")

# ------------------------------
# API DOCUMENTATION (Swagger/OpenAPI)
# ------------------------------
if DEBUG and not is_test_environment():
    SPECTACULAR_SETTINGS = {
        'TITLE': 'Claverica Fintech API',
        'DESCRIPTION': 'Fintech backend API documentation',
        'VERSION': API_VERSION,
        'SERVE_INCLUDE_SCHEMA': False,
        'COMPONENT_SPLIT_REQUEST': True,
        'SWAGGER_UI_SETTINGS': {
            'deepLinking': True,
            'persistAuthorization': True,
            'displayRequestDuration': True,
        },
    }

# ------------------------------
# LOGGING - ADD THROTTLE LOGGING
# ------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'test': {
            'format': '{asctime} {levelname} {module}: {message}',
            'style': '{',
        },
        'throttle': {
            'format': '{asctime} THROTTLE {user} {ip} {endpoint} {rate}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'test_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'test',
        },
        'throttle_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/throttle.log',
            'formatter': 'throttle',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'receipts': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'tests': {
            'handlers': ['test_console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'rest_framework_simplejwt': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'transfers': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'whitenoise': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'rest_framework.throttling': {
            'handlers': ['throttle_file', 'console'] if DEBUG else ['throttle_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = BASE_DIR / 'logs'
os.makedirs(logs_dir, exist_ok=True)

# ------------------------------
# FILE UPLOAD SETTINGS
# ------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# ------------------------------
# SESSION SETTINGS
# ------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ------------------------------
# EMAIL SETTINGS
# ------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_env_variable('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(get_env_variable('EMAIL_PORT', 587))
EMAIL_USE_TLS = get_env_variable('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = get_env_variable('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = get_env_variable('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ------------------------------
# TEST SETTINGS
# ------------------------------
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# ============================================================================
# CRITICAL: DIAGNOSTIC OUTPUT FOR USER MODEL DEBUGGING
# ============================================================================
print("=" * 60)
print("🚀 SYSTEM DIAGNOSTICS")
print("=" * 60)
print(f"🔧 AUTH_USER_MODEL: {AUTH_USER_MODEL}")
print(f"🐛 DEBUG: {DEBUG}")
print(f"🌐 ALLOWED_HOSTS: {ALLOWED_HOSTS}")
print(f"🗄️  DATABASE ENGINE: {DATABASES['default']['ENGINE']}")
print(f"📦 ACCOUNTS in INSTALLED_APPS: {'accounts' in INSTALLED_APPS}")
print(f"📌 ACCOUNTS position: {INSTALLED_APPS.index('accounts') if 'accounts' in INSTALLED_APPS else 'NOT FOUND'}")
print(f"📁 STATIC_ROOT: {STATIC_ROOT}")
print(f"📁 STATICFILES_DIRS: {STATICFILES_DIRS}")
print(f"📦 WHITENOISE ENABLED: {'whitenoise.middleware.WhiteNoiseMiddleware' in MIDDLEWARE}")
print(f"🔐 THROTTLE RATES: {REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']}")
print(f"💾 CACHE BACKEND: {CACHES['default']['BACKEND']}")
print(f"🌍 CORS ALLOWED ORIGINS: {CORS_ALLOWED_ORIGINS[:3]}..." if len(CORS_ALLOWED_ORIGINS) > 3 else f"🌍 CORS ALLOWED ORIGINS: {CORS_ALLOWED_ORIGINS}")
print(f"🔒 CSRF TRUSTED ORIGINS: {CSRF_TRUSTED_ORIGINS[:3]}..." if len(CSRF_TRUSTED_ORIGINS) > 3 else f"🔒 CSRF TRUSTED ORIGINS: {CSRF_TRUSTED_ORIGINS}")
print("=" * 60)
print("✅ Settings loaded successfully with throttle fixes!")
print("=" * 60)
# ============================================================================