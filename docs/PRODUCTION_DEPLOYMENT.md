# Ultra-Trader Production Deployment Guide

## Overview
This guide explains how to deploy Ultra-Trader in a production environment using Gunicorn WSGI server instead of Flask's development server.

## Problem Solved
**Before:** Flask development server showed warnings:
```
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
```

**After:** Production-ready Gunicorn WSGI server with no warnings and proper configuration.

## Production Setup

### 1. Requirements
The production deployment uses minimal dependencies:
```
flask==3.1.1
gunicorn==23.0.0
python-telegram-bot==20.7
```

### 2. Gunicorn Configuration
Production settings are defined in `gunicorn.conf.py`:
- **Workers:** 1 (optimized for resource efficiency)
- **Timeout:** 30 seconds
- **Logging:** INFO level to stdout/stderr
- **Port:** Dynamic from environment variable `$PORT` (defaults to 5000)
- **Security:** Request limits and graceful timeouts

### 3. Deployment Commands

#### Local Development (with warnings):
```bash
python optimized_deployment_entry.py
```

#### Production Deployment (recommended):
```bash
gunicorn -c gunicorn.conf.py optimized_deployment_entry:app
```

#### Platform-as-a-Service (Heroku, Render, etc.):
Uses `Procfile`:
```
web: gunicorn -c gunicorn.conf.py optimized_deployment_entry:app
```

#### Docker Production:
```bash
docker build -t ultra-trader-prod .
docker run -p 5000:5000 ultra-trader-prod
```

### 4. Environment Variables
- `PORT`: Server port (default: 5000)
- All other environment variables remain the same

### 5. Health Monitoring
The production setup includes health monitoring endpoints:

- **Health Check:** `GET /health`
  ```json
  {"status": "healthy", "port": 5000, "deployment": "production_ready"}
  ```

- **System Status:** `GET /api/status`
  ```json
  {
    "system": "active",
    "deployment": "minimal", 
    "docker_optimized": true,
    "port": 5000,
    "image_size": "<500MB"
  }
  ```

### 6. Features Preserved
- ✅ Ultra-minimal Docker image (<500MB)
- ✅ Single port configuration
- ✅ All existing API endpoints
- ✅ Dashboard functionality
- ✅ Health check endpoints
- ✅ Production-ready logging

### 7. Security & Performance
- **Workers:** Configured for optimal resource usage
- **Timeouts:** Proper request handling timeouts
- **Logging:** Structured logging for monitoring
- **Graceful Restart:** Handles deployment updates smoothly
- **Request Limits:** Protects against malformed requests

### 8. Troubleshooting

#### No Development Server Warnings
✅ **Fixed:** Replaced `app.run()` with Gunicorn WSGI server

#### Container Stopping Issues
✅ **Fixed:** Proper Gunicorn configuration with health checks and graceful timeouts

#### Performance in Production
✅ **Optimized:** Single worker for resource efficiency, can be scaled up as needed

### 9. Scaling Recommendations

For higher traffic, modify `gunicorn.conf.py`:
```python
workers = 2  # Increase for more concurrent requests
worker_connections = 2000  # Higher connection limit
```

### 10. Monitoring
Monitor these metrics in production:
- Response times via access logs
- Worker restarts via error logs  
- Health check endpoint availability
- Container resource usage

## Quick Verification
After deployment, verify no warnings appear:
1. Start the production server
2. Check logs for absence of development server warnings
3. Test health endpoints: `/health` and `/api/status`
4. Verify dashboard loads at root URL `/`

## Support
For issues with production deployment, check:
1. Gunicorn logs for worker issues
2. Health check endpoint responses
3. Container/process resource usage
4. Environment variable configuration