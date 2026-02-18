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

# ✅ ADD THIS - Run migrations first!
python manage.py migrate --noinput

# Then run Django check
python manage.py check --deploy
CHECK_RESULT=$?

# ==============================================================================
# TEMPLATE DEBUGGING - Check if email templates exist (SAFE VERSION)
# ==============================================================================
echo "=== Checking template directories ==="
echo "Current directory: $(pwd)"
echo "Looking for email templates..."

# Try multiple possible paths
for path in \
    "accounts/templates/accounts/email" \
    "../accounts/templates/accounts/email" \
    "/app/accounts/templates/accounts/email" \
    "/app/backend/accounts/templates/accounts/email"; do
    if [ -d "$path" ]; then
        echo "✅ Found templates at: $path"
        ls -la "$path" 2>/dev/null || echo "   (empty directory)"
    else
        echo "❌ No templates at: $path"
    fi
done

echo "Searching for all template files:"
find . -path "*/templates/*/*.html" -type f 2>/dev/null | head -20 || echo "No template files found"
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