#!/bin/bash
set -e

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
