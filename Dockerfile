FROM python:3.12-slim

# Встановлюємо wget
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY bot/ ./bot/
COPY services/ ./services/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]