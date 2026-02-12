FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/backend

# CRITICAL: Force create start.sh with CORRECT PORT syntax
RUN rm -f start.sh && \
    echo '#!/bin/bash' > start.sh && \
    echo 'echo "=== STARTING CLOVERICA BACKEND ==="' >> start.sh && \
    echo 'echo "Current directory: D:\Erustus\claverica-backend"' >> start.sh && \
    echo 'echo "Script location: "' >> start.sh && \
    echo 'echo "PORT: \"' >> start.sh && \
    echo '' >> start.sh && \
    echo 'cd /app/backend' >> start.sh && \
    echo 'echo "Changed to: D:\Erustus\claverica-backend"' >> start.sh && \
    echo '' >> start.sh && \
    echo 'export PYTHONPATH=/app:/app/backend' >> start.sh && \
    echo 'export DJANGO_SETTINGS_MODULE=backend.settings' >> start.sh && \
    echo 'export SECRET_KEY="\"' >> start.sh && \
    echo '' >> start.sh && \
    echo 'echo "Running database migrations..."' >> start.sh && \
    echo 'python manage.py migrate --noinput' >> start.sh && \
    echo '' >> start.sh && \
    echo 'echo "Collecting static files..."' >> start.sh && \
    echo 'python manage.py collectstatic --noinput' >> start.sh && \
    echo '' >> start.sh && \
    echo 'echo "Starting gunicorn on port \..."' >> start.sh && \
    echo 'exec gunicorn backend.wsgi:application \' >> start.sh && \
    echo '    --bind 0.0.0.0:\ \' >> start.sh && \
    echo '    --workers 2 \' >> start.sh && \
    echo '    --timeout 120 \' >> start.sh && \
    echo '    --access-logfile - \' >> start.sh && \
    echo '    --error-logfile - \' >> start.sh && \
    echo '    --log-level info' >> start.sh && \
    chmod +x start.sh

RUN python manage.py collectstatic --noinput

CMD ["./start.sh"]
