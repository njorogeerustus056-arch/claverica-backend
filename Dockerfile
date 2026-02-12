FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY the backend directory
COPY backend/ ./backend/

WORKDIR /app/backend

# DO NOT RECREATE START.SH - IT'S ALREADY CORRECT IN YOUR BACKEND FOLDER!
RUN chmod +x start.sh

RUN python manage.py collectstatic --noinput

CMD ["./start.sh"]
