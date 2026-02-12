#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: \D:\Erustus\claverica-backend"
echo "Script location: \"
echo "PORT: \"

cd /app/backend || cd backend || echo "Already in backend directory"
echo "Changed to: \D:\Erustus\claverica-backend"

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings_railway

# RUN MIGRATIONS
echo "Running database migrations..."
python manage.py migrate --noinput

# COLLECT STATIC FILES
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:\ \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
