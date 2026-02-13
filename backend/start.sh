#!/bin/bash
set -x
echo "STARTING"
python manage.py check --deploy
if [ $? -eq 0 ]; then
    exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT
else
    exit 1
fi
