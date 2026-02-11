#!/bin/bash
set -e

echo "=== Starting Django on Railway ==="

# Set environment
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH=/app/backend:/app:$PYTHONPATH

# Change to backend directory where manage.py is
cd /app/backend

# Run migrations if needed
python manage.py migrate --noinput || echo "Migrations skipped/failed"

# Start Gunicorn
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
