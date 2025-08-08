"""
Gunicorn Production Configuration for Ultra-Trader
Optimized for deployment with proper production settings
"""

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = 1  # Minimal for resource efficiency
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "ultra-trader"

# Server mechanics
daemon = False
pidfile = None
tmp_upload_dir = None

# SSL (disabled for simplicity, can be enabled if needed)
keyfile = None
certfile = None

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
sendfile = False

# Graceful restart
graceful_timeout = 30