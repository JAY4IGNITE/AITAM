# Dockerfile for FastAPI Backend (Render & Container compatible)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (libzbar for QR code scanning)
RUN apt-get update && apt-get install -y \
    gcc \
    libzbar0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PORT=8000

# Respect Render's dynamic $PORT environment variable
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
