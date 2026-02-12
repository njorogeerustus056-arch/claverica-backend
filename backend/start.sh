#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: \D:\Erustus\claverica-backend\backend"
echo "Script location: \"
echo "PORT: \"

cd /app/backend
echo "Changed to: \D:\Erustus\claverica-backend\backend"

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings

# RUN MIGRATIONS
echo "Running database migrations..."
python manage.py migrate --noinput

# COLLECT STATIC FILES
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:\ \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info

# Deployment timestamp: 2026-02-12 07:41:40
