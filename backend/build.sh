#!/bin/bash
set -e

echo "=== Railway Build Starting ==="
echo "Working directory: $(pwd)"

# Virtual environment path (Railway uses /app/.venv)
VENV_PYTHON="/app/.venv/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "WARNING: Virtual environment not found at $VENV_PYTHON"
    # Try to find Python
    VENV_PYTHON=$(find /app -name "python" -type f 2>/dev/null | head -1)
    if [ -z "$VENV_PYTHON" ]; then
        echo "ERROR: No Python found!"
        exit 1
    fi
    echo "Found Python at: $VENV_PYTHON"
fi

# Set Django environment
export DJANGO_SETTINGS_MODULE=backend.settings
export PYTHONPATH=/app/backend:/app:$PYTHONPATH

echo "=== Collecting static files ==="
cd /app/backend
$VENV_PYTHON manage.py collectstatic --noinput

echo "✅ Build completed successfully!"