#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: $(pwd)"
echo "Script location: $(dirname $0)"
echo "PORT: $PORT"

# Ensure we're in the right directory
cd /app/backend
echo "Changed to: $(pwd)"

# Set Python path
export PYTHONPATH=/app:/app/backend

# Check if gunicorn is installed
echo "Checking gunicorn..."
which gunicorn || echo "Gunicorn not found in PATH"

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
