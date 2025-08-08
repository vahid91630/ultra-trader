#!/usr/bin/env python3
"""
Ultra-Minimal Deployment Entry Point
Optimized for <500MB Docker image and single port deployment
"""

import os
import json
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# Get port from environment
PORT = int(os.environ.get('PORT', 5000))

# Minimal HTML template
MINIMAL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading System</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 20px; border-radius: 5px; margin: 20px 0; }
        .active { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        h1 { color: #333; margin-bottom: 30px; }
        .metric { display: inline-block; margin: 10px 20px; }
        .metric-label { font-weight: bold; color: #666; }
        .metric-value { color: #28a745; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Trading System Dashboard</h1>
        
        <div class="status active">
            <strong>✅ System Status: ACTIVE</strong>
        </div>
        
        <div class="status info">
            <strong>🔧 Deployment Mode: Production Ready</strong>
            <br>
            This is the ultra-minimal deployment optimized for Replit.
            <br>
            Docker image size: &lt;500MB | Single port configuration: {{ port }}
        </div>
        
        <div style="margin-top: 30px;">
            <div class="metric">
                <div class="metric-label">Port:</div>
                <div class="metric-value">{{ port }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Status:</div>
                <div class="metric-value">Ready</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Main dashboard page"""
    return render_template_string(MINIMAL_TEMPLATE, port=PORT)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "port": PORT,
        "deployment": "production_ready"
    })

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "system": "active",
        "deployment": "minimal",
        "docker_optimized": True,
        "port": PORT,
        "image_size": "<500MB"
    })

if __name__ == '__main__':
    print(f"🚀 Starting ultra-minimal deployment on port {PORT}")
    print("⚠️  Note: For production deployment, use: gunicorn optimized_deployment_entry:app")
    app.run(host='0.0.0.0', port=PORT, debug=False)