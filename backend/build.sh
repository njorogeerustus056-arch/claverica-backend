#!/bin/bash
set -e

echo "=== Railway Build Starting ==="
echo "Working directory: $(pwd)"

# Check if we're in the right place
if [ ! -f "manage.py" ]; then
    echo "ERROR: manage.py not found in $(pwd)"
    echo "Contents:"
    ls -la
    exit 1
fi

# Check virtual environment
if [ ! -f "/opt/venv/bin/python" ]; then
    echo "ERROR: Virtual environment not found at /opt/venv/bin/python"
    exit 1
fi

# Set Django environment
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH=/app:$PYTHONPATH

# Use venv Python
PYTHON="/opt/venv/bin/python"
PIP="/opt/venv/bin/pip"

echo "Python: $($PYTHON --version)"
echo "Pip: $($PIP --version)"

echo "=== Collecting static files ==="
$PYTHON manage.py collectstatic --noinput

echo "✅ Build completed successfully!"
