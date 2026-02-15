FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# code
COPY . /app

# Cloud Run sets $PORT (default 8080). Must listen on it.
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
