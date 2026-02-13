#!/bin/bash
set -x  # Print every command
echo "=== STARTING WITH DEBUG ==="
echo "PORT: $PORT"
echo "PYTHONPATH: $PYTHONPATH"
echo "Current directory: $(pwd)"
ls -la

echo "=== Testing Django ==="
python -c "
import sys
print('Python version:', sys.version)
print('Path:', sys.path)
try:
    from django.conf import settings
    print('Django version:', django.get_version())
    print('Settings module:', settings.SETTINGS_MODULE)
    print('SECRET_KEY set:', bool(settings.SECRET_KEY))
    print('DATABASES:', list(settings.DATABASES.keys()))
except Exception as e:
    print('CRASH:', e)
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo "=== Starting Gunicorn ==="
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 1 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug
