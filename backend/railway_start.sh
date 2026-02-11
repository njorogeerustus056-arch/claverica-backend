#!/bin/bash
set -e

echo "=== Starting Django on Railway ==="

# Set environment variables for Railway
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH=/app:$PYTHONPATH

# Run migrations if needed
cd /app
python manage.py migrate --noinput || echo "Migrations failed, continuing..."

# Start Gunicorn
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
