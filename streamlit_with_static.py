#!/usr/bin/env python3
"""
Static file server for Streamlit to handle apple-touch-icon and favicon requests
"""
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

class StaticFileHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/runner/work/ultra-trader/ultra-trader", **kwargs)
    
    def do_GET(self):
        # Handle specific icon requests
        if self.path == '/apple-touch-icon.png':
            self.path = '/apple-touch-icon.png'
        elif self.path == '/favicon.ico':
            self.path = '/static/icons/favicon-32x32.png'
        elif self.path.startswith('/static/'):
            # Keep static paths as is
            pass
        else:
            # Let other requests go through normally
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Not Found')
            return
            
        return super().do_GET()

def start_static_server(port=8001):
    """Start a simple static file server for icons"""
    try:
        server = HTTPServer(('0.0.0.0', port), StaticFileHandler)
        print(f"Static file server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Static server error: {e}")

if __name__ == "__main__":
    # Start static server in background thread
    static_thread = threading.Thread(target=start_static_server, daemon=True)
    static_thread.start()
    
    # Run Streamlit dashboard
    os.system("streamlit run ultra_dashboard/dashboard.py --server.enableCORS false --server.port $PORT")