FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY the backend directory
COPY backend/ ./backend/

WORKDIR /app/backend

# DO NOT recreate start.sh - use the CORRECT one from backend folder
RUN chmod +x start.sh

RUN python manage.py collectstatic --noinput

CMD ["./start.sh"]
