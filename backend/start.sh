#!/bin/bash
set -e
echo "=== STARTING CLOVERICA BACKEND ==="

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings

# Start Gunicorn directly (migrations can run in background if needed)
PORT="${PORT:-8000}"
echo "Starting Gunicorn on port $PORT"
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
