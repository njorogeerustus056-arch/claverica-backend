#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: $(pwd)"
echo "PORT: $PORT"

# Set Python path
export PYTHONPATH=/app:/app/backend

# Start gunicorn - no cd needed since we're already in /app/backend
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
