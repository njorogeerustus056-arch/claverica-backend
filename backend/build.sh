#!/bin/bash
set -e

# Set the correct Django settings module
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH=/app:$PYTHONPATH

# Use the virtual environment Python directly (NO 'source' or '.' needed)
PYTHON=/opt/venv/bin/python
PIP=/opt/venv/bin/pip

echo "=== Installing dependencies ==="
$PIP install --upgrade pip
$PIP install -r requirements.txt

echo "=== Collecting static files ==="
$PYTHON manage.py collectstatic --noinput

echo "=== Running migrations ==="
$PYTHON manage.py migrate --noinput

echo "=== Creating cache tables ==="
$PYTHON manage.py createcachetable || echo "Cache table creation skipped"

echo "=== Build complete ==="