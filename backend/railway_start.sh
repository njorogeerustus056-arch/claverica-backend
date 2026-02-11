#!/bin/bash
set -e

echo "=== Railway Startup Debug ==="
echo "PORT: $PORT"
echo "PWD: $(pwd)"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Check if in app directory
if [ ! -f "manage.py" ]; then
    echo "ERROR: manage.py not found! Changing to /app..."
    cd /app
fi

echo "Directory contents:"
ls -la

# Test Django
echo "Testing Django import..."
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
    print(f'ERROR loading settings: {e}')
    import traceback
    traceback.print_exc()
"

echo "=== Starting Gunicorn ==="

# Start Gunicorn with debug
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug
