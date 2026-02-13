#!/bin/bash
set -x
echo "STARTING"
echo "Current directory: D:\Erustus\claverica-backend\backend"
echo "PORT: "

# Set Python path explicitly
export PYTHONPATH=/app:/app/backend

# Change to the backend directory
cd /app/backend

# Run Django check
python manage.py check --deploy
CHECK_RESULT=True

if [  -eq 0 ]; then
    echo "Django check passed, starting Gunicorn"
    exec gunicorn backend.wsgi:application \
        --bind 0.0.0.0: \
        --workers 1 \
        --threads 1 \
        --timeout 60 \
        --access-logfile - \
        --error-logfile - \
        --pythonpath /app \
        --pythonpath /app/backend
else
    echo "Django check failed with code "
    exit 1
fi