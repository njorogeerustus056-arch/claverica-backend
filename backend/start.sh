#!/bin/bash
set -e

echo "=== Railway Startup Debug ==="
echo "PORT: $PORT"
echo "PWD: $(pwd)"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# List directory to debug
echo "Directory contents:"
ls -la

# Change to backend directory
cd /app/backend
echo "Changed to: $(pwd)"
echo "Backend contents:"
ls -la

# Test Django
echo "Testing Django..."
python -c "import django; print(f'Django {django.__version__}')"

# Test settings
echo "Testing settings..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
try:
    from django.conf import settings
    print(f'DEBUG: {settings.DEBUG}')
    print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
"

echo "=== Starting Gunicorn ==="

# Start Gunicorn
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
