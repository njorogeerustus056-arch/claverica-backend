"""
Django settings for Claverica fintech backend.
Production-ready configuration for Render deployment.
"""

import os
from pathlib import Path
from decimal import Decimal
from datetime import timedelta
import dj_database_url

# ------------------------------
# BASE DIRECTORY
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# SECRET KEY AND DEBUG
# ------------------------------
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-CHANGE-THIS-IN-PRODUCTION'
)
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ------------------------------
# API VERSION (Added - fixes the 500 error on root endpoint)
# ------------------------------
API_VERSION = os.environ.get('API_VERSION', '1.0.0')  # You can override via env var on Render if needed

# ------------------------------
# ALLOWED HOSTS (Improved for Render)
# ------------------------------
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Always include Render's external hostname
render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
    ALLOWED_HOSTS.append(f'.{render_hostname}')  # For wildcard subdomains if needed

# Optional: For quick testing (remove after fixing)
# ALLOWED_HOSTS.append('*')

# ------------------------------
# INSTALLED APPS
# ------------------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',

    # Project apps
    'Tasks',
    'accounts',  # accounts app
    'cards',
    'compliance',
    'crypto',
    'escrow',
    'notifications',
    'payments',
    'receipts',
    'transactions',
]

# ------------------------------
# MIDDLEWARE
# ------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ------------------------------
# URLS AND TEMPLATES
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
ASGI_APPLICATION = 'backend.asgi.application'

# ------------------------------
# DATABASE - Smart config for local SQLite and Render Postgres
# ------------------------------
database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith('sqlite://'):
    # Local development with SQLite (uses your existing db.sqlite3)
    DATABASES = {
        'default': dj_database_url.parse(database_url)
    }
else:
    # Production on Render (Postgres with SSL)
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            ssl_require=not DEBUG,  # SSL in prod, optional in debug
        )
    }

# ------------------------------
# AUTH PASSWORD VALIDATORS
# ------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------
# INTERNATIONALIZATION
# ------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------------
# STATIC AND MEDIA FILES
# ------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------------------
# DEFAULT AUTO FIELD
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------
# REST FRAMEWORK
# ------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# ------------------------------
# SIMPLE JWT
# ------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ------------------------------
# CORS
# ------------------------------
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# ------------------------------
# SECURITY
# ------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000,http://localhost:5173'
).split(',')
if render_hostname:
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_hostname}')

# ------------------------------
# RECEIPT SETTINGS
# ------------------------------
RECEIPT_STORAGE_PATH = MEDIA_ROOT / 'receipts'
RECEIPT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

ALLOWED_RECEIPT_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
]

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
# Suppress DRF min_value warning (optional, for clean logs)
# ------------------------------
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="rest_framework.fields")
