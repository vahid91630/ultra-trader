import os
import sys

if __name__ == "__main__":
    print("✅ Ultra Trader Dashboard Booted")
    
    # Check if running in production environment
    is_production = os.environ.get('ENVIRONMENT', 'development').lower() == 'production'
    
    if is_production:
        print("⚠️  Production Mode: Streamlit development server is not recommended for production.")
        print("📘 Consider migrating to Flask/FastAPI or use a proper Streamlit deployment method.")
        print("🔗 See: https://docs.streamlit.io/deploy")
    
    # Use proper Streamlit server configuration
    port = os.environ.get('PORT', '8501')
    
    # Build the streamlit command with production-friendly settings
    streamlit_cmd = [
        "streamlit", "run", "ultra_dashboard/dashboard.py",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.runOnSave", "false",
        "--server.allowRunOnSave", "false"
    ]
    
    if is_production:
        print(f"🚀 Starting Streamlit with production settings on port {port}")
    else:
        print(f"🔧 Starting Streamlit in development mode on port {port}")
    
    # Execute the command
    os.execvp("streamlit", streamlit_cmd)
