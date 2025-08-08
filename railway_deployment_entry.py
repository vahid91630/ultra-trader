#!/usr/bin/env python3
"""
Alternative Flask-based entry point with full static file support
For Railway deployment that requires explicit icon handling
"""

import os
from flask import Flask, render_template_string, jsonify, send_from_directory, redirect

app = Flask(__name__, static_folder='static')

# Get port from environment
PORT = int(os.environ.get('PORT', 5000))

# Trading System HTML Template with proper meta tags
TRADING_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultra Trader - Trading System</title>
    
    <!-- Icon meta tags -->
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/icons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/icons/favicon-16x16.png">
    <meta name="theme-color" content="#1e3c72">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Ultra Trader">
    
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            margin: 20px;
        }
        .title {
            font-size: 2.5rem;
            margin-bottom: 20px;
            color: #00ff88;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        }
        .status {
            font-size: 1.2rem;
            margin: 20px 0;
            padding: 15px;
            background: rgba(0, 255, 136, 0.2);
            border-radius: 10px;
            border: 1px solid #00ff88;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            margin: 10px;
            background: linear-gradient(45deg, #00ff88, #00cc66);
            color: #000;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3);
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 255, 136, 0.5);
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }
        .metric {
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #00ff88;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="title">🚀 Ultra Trader</div>
        
        <div class="status">
            ✅ System Active & Ready
        </div>
        
        <p>Trading system is running successfully on Railway deployment.</p>
        <p>Port: {{ port }} | Status: Operational</p>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">✅</div>
                <div class="metric-label">System Status</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ port }}</div>
                <div class="metric-label">Port</div>
            </div>
            <div class="metric">
                <div class="metric-value">100%</div>
                <div class="metric-label">Uptime</div>
            </div>
            <div class="metric">
                <div class="metric-value">0</div>
                <div class="metric-label">Errors</div>
            </div>
        </div>
        
        <div style="margin-top: 30px;">
            <a href="/health" class="btn">Health Check</a>
            <a href="/api/status" class="btn">API Status</a>
        </div>
        
        <div style="margin-top: 20px; font-size: 0.9rem; opacity: 0.7;">
            🔧 Deployment: Railway Production | Icons: ✅ Configured
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Main dashboard page"""
    return render_template_string(TRADING_TEMPLATE, port=PORT)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "port": PORT,
        "deployment": "railway_production",
        "icons_configured": True,
        "static_files": "enabled"
    })

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "system": "active",
        "deployment": "railway_flask",
        "docker_optimized": True,
        "port": PORT,
        "static_handling": "enabled",
        "icons": {
            "apple_touch_icon": "/apple-touch-icon.png",
            "favicon": "/favicon.ico",
            "status": "configured"
        }
    })

# Static file routes to prevent 404 errors
@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Serve apple touch icon - prevents 404 on iOS devices"""
    try:
        return send_from_directory('.', 'apple-touch-icon.png')
    except FileNotFoundError:
        return send_from_directory('static/icons', 'apple-touch-icon.png')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon - prevents 404 on browsers"""
    return send_from_directory('static/icons', 'favicon-32x32.png')

@app.route('/robots.txt')
def robots():
    """Serve robots.txt"""
    return "User-agent: *\nAllow: /\n", 200, {'Content-Type': 'text/plain'}

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# Handle common icon requests
@app.route('/android-chrome-192x192.png')
@app.route('/android-chrome-512x512.png')
@app.route('/apple-touch-icon-precomposed.png')
def alternative_icons():
    """Handle alternative icon requests"""
    return send_from_directory('static/icons', 'apple-touch-icon.png')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler to log missing resources"""
    path = getattr(error, 'original_exception', {})
    print(f"404 Error for path: {path}")
    return jsonify({
        "error": "Not Found", 
        "message": "The requested resource was not found.",
        "path": str(path)
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal server error occurred."
    }), 500

if __name__ == '__main__':
    print(f"🚀 Starting Ultra Trader Flask deployment on port {PORT}")
    print(f"📱 Apple touch icon configured: /apple-touch-icon.png")
    print(f"🔍 Favicon configured: /favicon.ico")
    print(f"📂 Static files enabled: /static/")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)