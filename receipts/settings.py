# Add to your Django settings.py

INSTALLED_APPS = [
    # ... your existing apps
    'rest_framework',
    'corsheaders',
    'receipts',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... your existing middleware
]

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://your-frontend-domain.com",  # Add your Render frontend URL
]

CORS_ALLOW_CREDENTIALS = True

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
