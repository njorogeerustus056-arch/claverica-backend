FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

WORKDIR /app/backend

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV PYTHONPATH=/app:/app/backend
ENV RAILWAY=true

# Make start.sh executable
RUN chmod +x start.sh

# Skip collectstatic during build - it will run in start.sh instead
# This avoids the AppRegistryNotReady error
RUN echo "Skipping collectstatic during build - will run at runtime"

# No CMD - Railway will use start.sh