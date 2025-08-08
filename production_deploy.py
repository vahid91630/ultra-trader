#!/usr/bin/env python3
"""
Production Deployment Entry Point for Ultra-Trader
Chooses the appropriate production server based on application type
"""

import os
import sys
import subprocess
import signal
import time
from typing import Optional

class ProductionDeployment:
    def __init__(self):
        self.port = int(os.environ.get('PORT', 5000))
        self.app_type = os.environ.get('APP_TYPE', 'flask').lower()
        self.environment = os.environ.get('ENVIRONMENT', 'production')
        self.process: Optional[subprocess.Popen] = None
        
    def signal_handler(self, signum, frame):
        """Graceful shutdown handler"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("⚠️  Process didn't terminate gracefully, forcing kill...")
                self.process.kill()
        sys.exit(0)
    
    def run_flask_production(self):
        """Run Flask app with Gunicorn"""
        print(f"🚀 Starting Flask app with Gunicorn on port {self.port}")
        
        # Determine which Flask app to run
        flask_app = "optimized_deployment_entry:app"
        if os.path.exists("fast_dashboard.py"):
            print("📊 Using fast_dashboard as main application")
            flask_app = "fast_dashboard:app"
        
        cmd = [
            "gunicorn",
            "-c", "gunicorn.conf.py",
            flask_app
        ]
        
        print(f"🔧 Command: {' '.join(cmd)}")
        return subprocess.Popen(cmd)
    
    def run_streamlit_production(self):
        """Run Streamlit app with production settings"""
        print(f"🎯 Starting Streamlit app on port {self.port}")
        print("⚠️  Note: Streamlit development server - consider Flask migration for production")
        
        cmd = [
            "streamlit", "run", "ultra_dashboard/dashboard.py",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false", 
            "--server.port", str(self.port),
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.runOnSave", "false",
            "--server.allowRunOnSave", "false"
        ]
        
        print(f"🔧 Command: {' '.join(cmd)}")
        return subprocess.Popen(cmd)
    
    def health_check(self) -> bool:
        """Basic health check for the running application"""
        try:
            import urllib.request
            import urllib.error
            
            # Try multiple health endpoints
            health_endpoints = [
                f"http://localhost:{self.port}/health",
                f"http://localhost:{self.port}/api/status",
                f"http://localhost:{self.port}/"
            ]
            
            for url in health_endpoints:
                try:
                    with urllib.request.urlopen(url, timeout=5) as response:
                        if response.getcode() == 200:
                            return True
                except (urllib.error.URLError, urllib.error.HTTPError):
                    continue
            
            return False
        except Exception:
            return False
    
    def run(self):
        """Main deployment function"""
        print("🌟 Ultra-Trader Production Deployment Starting...")
        print(f"📋 Environment: {self.environment}")
        print(f"🔧 App Type: {self.app_type}")
        print(f"🌐 Port: {self.port}")
        print("="*50)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Choose appropriate server based on app type
            if self.app_type == 'streamlit':
                self.process = self.run_streamlit_production()
            else:
                self.process = self.run_flask_production()
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Basic health check
            if self.health_check():
                print("✅ Application started successfully and health check passed")
            else:
                print("⚠️  Application started but health check failed")
            
            print(f"🌐 Application available at: http://0.0.0.0:{self.port}")
            print("🔄 Monitoring application... (Press Ctrl+C to stop)")
            
            # Wait for the process to complete
            self.process.wait()
            
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        except Exception as e:
            print(f"❌ Error during deployment: {e}")
            sys.exit(1)
        finally:
            if self.process:
                self.process.terminate()
                
        print("👋 Deployment stopped")

if __name__ == '__main__':
    deployment = ProductionDeployment()
    deployment.run()