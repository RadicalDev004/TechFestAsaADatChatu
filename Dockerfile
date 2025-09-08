# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
# Make sure requirements.txt includes: fastapi and hypercorn
# (You can remove gunicorn/uvicorn/eventlet from it.)
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# (optional) run as non-root
RUN useradd -m appuser
USER appuser

EXPOSE 5000

# Hypercorn runs ASGI apps directly
# Adjust "main:app" if your module/object differs
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-log", "-"]
