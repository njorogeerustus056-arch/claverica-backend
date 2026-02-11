FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

WORKDIR /app/backend

# Collect static files
RUN python manage.py collectstatic --noinput

# Make start script executable
RUN chmod +x start.sh

# Use start.sh
CMD ["./start.sh"]
