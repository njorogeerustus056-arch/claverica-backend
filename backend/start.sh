#!/bin/bash
set -x
echo "STARTING"
echo "Current directory: $(pwd)"
echo "PORT: $PORT"

# Set Python path explicitly
export PYTHONPATH=/app:/app/backend

# Change to the backend directory
cd /app/backend

# Run Django check and capture ONLY the exit code (not the output)
python manage.py check --deploy > /dev/null 2>&1
CHECK_RESULT=$?

if [ $CHECK_RESULT -eq 0 ]; then
    echo "Django check passed, starting Gunicorn"
    # Add delay to ensure Railway health check doesn't timeout
    sleep 5
    exec gunicorn backend.wsgi:application \
        --bind 0.0.0.0:$PORT \
        --workers 1 \
        --threads 1 \
        --timeout 120 \
        --graceful-timeout 30 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --access-logfile - \
        --error-logfile - \
        --pythonpath /app \
        --pythonpath /app/backend
else
    echo "Django check failed with code $CHECK_RESULT"
    exit 1
fi