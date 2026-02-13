#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: $(pwd)"
echo "PORT: ${PORT:-8000}"
echo "RAILWAY: ${RAILWAY:-Not set}"

export PYTHONPATH=/app:/app/backend
export DJANGO_SETTINGS_MODULE=backend.settings

echo "=== PYTHON PATH ==="
python -c "import sys; print('\n'.join(sys.path))"

echo "=== INSTALLED PACKAGES ==="
pip list

echo "=== RUNNING MIGRATIONS ==="
python manage.py migrate --noinput

echo "=== COLLECTING STATIC FILES ==="
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
echo "=== STARTING GUNICORN ON PORT $PORT ==="

exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info