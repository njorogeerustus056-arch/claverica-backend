FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

WORKDIR /app/backend

RUN chmod +x start.sh

RUN python manage.py collectstatic --noinput

# IMPORTANT: Remove the CMD line entirely - Railway will use start.sh
# Just delete or comment out this line:
# CMD ["./start.sh"]