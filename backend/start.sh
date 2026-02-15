#!/bin/bash
set -x
echo "STARTING"
echo "Current directory: $(pwd)"
echo "PORT: $PORT"
echo "Python version: $(python --version)"

# Set Python path explicitly
export PYTHONPATH=/app:/app/backend

# Change to the backend directory
cd /app/backend

# Run Django check
python manage.py check --deploy
CHECK_RESULT=$?

# ==============================================================================
# TEMPLATE DEBUGGING - Check if email templates exist
# ==============================================================================
echo "=== Checking template directories ==="
echo "Current directory: $(pwd)"
echo "Listing accounts/templates/accounts/email/:"
ls -la accounts/templates/accounts/email/ 2>/dev/null || echo "No templates found in accounts/templates/accounts/email/"
echo "Listing all template paths:"
find . -path "*/templates/*/email/*.html" -type f 2>/dev/null || echo "No template files found"
echo "=== End template check ==="
# ==============================================================================

if [ $CHECK_RESULT -eq 0 ]; then
    echo "Django check passed, starting Gunicorn"

    # CRITICAL: Increased delay to ensure Railway health check system is ready
    echo "Waiting 15 seconds for Railway health check system..."
    sleep 15

    # Optimized Gunicorn settings to prevent worker timeouts
    exec gunicorn backend.wsgi:application \
        --bind 0.0.0.0:$PORT \
        --workers 2 \
        --threads 2 \
        --timeout 60 \
        --graceful-timeout 30 \
        --max-requests 500 \
        --max-requests-jitter 50 \
        --access-logfile - \
        --error-logfile - \
        --pythonpath /app \
        --pythonpath /app/backend \
        --preload \
        --worker-class sync
else
    echo "Django check failed with code $CHECK_RESULT"
    exit 1
fi