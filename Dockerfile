FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend directory only, not the root
COPY backend/ ./backend/

WORKDIR /app/backend

# Use the CORRECT start.sh from backend folder
RUN chmod +x start.sh

RUN python manage.py collectstatic --noinput

CMD ["./start.sh"]
