#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: D:\Erustus\claverica-backend\backend"
echo "Script location: "
echo "PORT: "

cd /app/backend
echo "Changed to: D:\Erustus\claverica-backend\backend"

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings_railway

# RUN MIGRATIONS - THIS FIXES THE 500 ERROR!
echo "Running database migrations..."
python manage.py migrate

echo "Starting gunicorn..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0: \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
