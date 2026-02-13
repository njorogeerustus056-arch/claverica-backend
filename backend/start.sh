#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings

# Run migrations in background
python manage.py migrate --noinput &

# Start Gunicorn IMMEDIATELY
PORT="${PORT:-8000}"
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
