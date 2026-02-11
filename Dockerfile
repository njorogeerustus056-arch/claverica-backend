FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Set working directory to backend
WORKDIR /app/backend

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE $PORT

# Start command with proper Python path
CMD cd /app/backend && PYTHONPATH=/app:/app/backend gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
