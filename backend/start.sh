#!/bin/bash
echo "=== STARTING CLOVERICA BACKEND ==="
echo "Current directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "PORT: $PORT"

# Set Python path
export PYTHONPATH=/app:/app/backend:$PYTHONPATH

# Start gunicorn
exec gunicorn backend.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
