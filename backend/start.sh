#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: $(pwd)"
echo "Script location: $(dirname $0)"
echo "PORT: $PORT"

cd /app/backend
echo "Changed to: $(pwd)"

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings_railway

echo "Starting gunicorn..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
