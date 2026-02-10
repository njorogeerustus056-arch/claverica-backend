#!/bin/bash
echo "=== Django Build Process ==="
echo "1. Applying database migrations..."
python manage.py migrate
echo "2. Collecting static files..."
python manage.py collectstatic --noinput
echo "3. Build completed successfully!"