# Railway Deployment Guide - Ultra Trader

## Overview
This project is configured for deployment on Railway using a Flask-based ultra-minimal application.

## Deployment Configuration

### Files for Railway Deployment:
- `Procfile` - Railway deployment command using gunicorn
- `requirements.txt` - Python dependencies including Flask and gunicorn
- `optimized_deployment_entry.py` - Main Flask application
- `Dockerfile` - Container configuration for Railway
- `railway.toml` - Railway-specific configuration

### Application Features:
- 🚀 Ultra-minimal Flask application (<500MB Docker image)
- 🏥 Health check endpoint at `/health`
- 📊 API status endpoint at `/api/status`
- 🎯 Automatic PORT environment variable handling
- 🔧 Production-ready with gunicorn WSGI server

### Endpoints:
- `/` - Main dashboard with trading system status
- `/health` - Health check for Railway monitoring
- `/api/status` - API status and system information

### Environment Variables:
- `PORT` - Automatically provided by Railway

### Testing Deployment Locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Test with gunicorn (production server)
PORT=8080 gunicorn optimized_deployment_entry:app --bind 0.0.0.0:8080

# Test endpoints
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/api/status
```

### Railway Deployment Process:
1. Railway detects the `Procfile` and uses it for deployment
2. Installs dependencies from `requirements.txt`
3. Starts the application using gunicorn
4. Automatically provides PORT environment variable
5. Health checks are performed on `/health` endpoint

### Benefits of This Configuration:
- ✅ Production-ready WSGI server (gunicorn)
- ✅ Proper port binding for Railway
- ✅ Health monitoring support
- ✅ Minimal resource usage
- ✅ Fast deployment and startup