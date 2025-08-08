# Ultra-minimal Dockerfile for Railway deployment <500MB
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Railway provides PORT environment variable
ENV PORT=5000

# Minimal system setup
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Copy application files
COPY optimized_deployment_entry.py .

# Railway will provide the PORT via environment variable
EXPOSE $PORT

# Health check for Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=2 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Use gunicorn for production deployment
CMD gunicorn optimized_deployment_entry:app --bind 0.0.0.0:$PORT
