#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: D:\Erustus\claverica-backend\backend"
echo "PORT: "
echo "RAILWAY: "

# Set Python path
export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings

# Print configuration status
echo "=== CONFIGURATION ==="
python -c "
import os
from django.conf import settings
print(f'SECRET_KEY set: {bool(settings.SECRET_KEY)}')
print(f'DEBUG: {settings.DEBUG}')
print(f'DATABASE: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
"

# Run migrations
echo "=== RUNNING MIGRATIONS ==="
python manage.py migrate --noinput

# Collect static files
echo "=== COLLECTING STATIC FILES ==="
python manage.py collectstatic --noinput

# Start gunicorn
echo "=== STARTING GUNICORN ON PORT  ==="
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0: \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info