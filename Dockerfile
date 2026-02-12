FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

WORKDIR /app/backend

RUN chmod +x start.sh

RUN python manage.py collectstatic --noinput

CMD ["./start.sh"]
