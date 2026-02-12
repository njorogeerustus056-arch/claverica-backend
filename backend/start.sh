#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: $(pwd)"
echo "Script location: $0"
echo "PORT: ${PORT:-8000}"

cd /app/backend
echo "Changed to: $(pwd)"

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings
export SECRET_KEY="${SECRET_KEY}"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn on port ${PORT:-8000}..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
