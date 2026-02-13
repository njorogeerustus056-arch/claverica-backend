#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: D:\Erustus\claverica-backend\backend"
echo "PORT: "
echo "RAILWAY: "

# CRITICAL: Set Python path correctly
export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings

# Print Python path for debugging
echo "=== PYTHON PATH ==="
python -c "import sys; print('\\n'.join(sys.path))"

echo "=== INSTALLED PACKAGES ==="
pip list

echo "=== RUNNING MIGRATIONS ==="
python manage.py migrate --noinput

echo "=== COLLECTING STATIC FILES ==="
python manage.py collectstatic --noinput

PORT="\"
echo "=== STARTING GUNICORN ON PORT \ ==="

exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:\ \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info