FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Create startup script to run migrations before starting the app
RUN echo '#!/bin/sh\n\
echo "Waiting for database..."\n\
while ! nc -z postgres 5432; do\n\
  sleep 1\n\
done\n\
echo "Database is ready!"\n\
echo "Running database migrations..."\n\
alembic upgrade head || echo "Migration failed or already applied"\n\
echo "Starting FastAPI server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]