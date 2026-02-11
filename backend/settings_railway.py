"""
Django settings for Railway deployment.
"""

from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*', '.up.railway.app']
ROOT_URLCONF = 'backend.urls'
ROOT_URLCONF = 'backend.urls'

# ==============================================================================
# CRITICAL: ROOT_URLCONF - THIS WAS MISSING!
# ==============================================================================
ROOT_URLCONF = 'backend.urls'  # <--- ADD THIS LINE!

# ==============================================================================
# DATABASE
# ==============================================================================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
    print("? Connected to PostgreSQL on Railway")
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',
        }
    }
    print("??  WARNING: No DATABASE_URL found, using temporary SQLite!")

# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
    'django_extensions',
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

WSGI_APPLICATION = 'backend.wsgi.application'

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
# STATIC FILES
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# AUTHENTICATION
# ==============================================================================
AUTH_USER_MODEL = 'accounts.Account'

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
# SECURITY
# ==============================================================================
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# DEFAULT PRIMARY KEY
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

