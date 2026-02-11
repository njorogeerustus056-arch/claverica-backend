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

# Make start.sh executable
RUN chmod +x /app/backend/start.sh

# Use absolute path to start.sh
CMD /app/backend/start.sh
