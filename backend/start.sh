#!/bin/bash
set -x
echo "=== STARTING ==="
echo "PORT: $PORT"

python manage.py check --deploy
CHECK_RESULT=$?

if [ $CHECK_RESULT -eq 0 ]; then
    echo "Django check passed, starting Gunicorn"
    exec gunicorn backend.wsgi:application \
        --bind 0.0.0.0:$PORT \
        --workers 1 \
        --threads 1 \
        --timeout 60 \
        --access-logfile - \
        --error-logfile -
else
    echo "Django check failed with code $CHECK_RESULT"
    exit 1
fi
