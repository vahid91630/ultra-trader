# Ultra-minimal Dockerfile for deployment <500MB
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Minimal system setup with SSL certificate handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /app

# Copy minimal requirements only
COPY requirements_deployment_minimal.txt requirements.txt

# Install Python packages with proper SSL handling
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt && \
    pip cache purge

# Copy single entry point
COPY optimized_deployment_entry.py .

# Single port exposure
EXPOSE 5000

# Minimal health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=2 \
  CMD curl -f http://localhost:5000/health || exit 1

# Use gunicorn for production deployment
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "--log-level", "info", "optimized_deployment_entry:app"]
