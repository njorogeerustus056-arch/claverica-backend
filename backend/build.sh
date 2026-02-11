#!/bin/bash
set -e

# CRITICAL: Activate the virtual environment that Nixpacks created
source /opt/venv/bin/activate

# Set the correct Django settings module
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH=/app:$PYTHONPATH

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Creating cache tables ==="
python manage.py createcachetable || echo "Cache table creation skipped"

echo "=== Build complete ==="