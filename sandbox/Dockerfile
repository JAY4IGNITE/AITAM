# Dockerfile for Sandbox Worker
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies for the worker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers (though the base image already has them)
RUN playwright install chromium

COPY . .

# Run the Celery worker or standalone python script to pull tasks from Redis
CMD ["celery", "-A", "browser_runner.worker", "worker", "--loglevel=info"]
