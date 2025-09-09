# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create app user early, so we can chown during COPY
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Minimal OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# App code (owned by appuser)
COPY --chown=appuser:appuser . .

# Make sure the data dir exists and is writable
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:5000", "--workers", "1", "--access-log", "-"]
