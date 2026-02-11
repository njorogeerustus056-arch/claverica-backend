"""
Django settings for Railway deployment.
"""

from pathlib import Path
import os
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['*', '.up.railway.app']

# ==============================================================================
# DATABASE - FIXED FOR RAILWAY!
# ==============================================================================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Railway PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
    print(f"? Connected to PostgreSQL on Railway")
else:
    # Fallback - but this will show error clearly
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',  # Changed to /tmp which is writable
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

# ... rest of your settings remain the same ...
