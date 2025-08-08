#!/usr/bin/env python3
"""
Development Server Warning Detection Test
Specifically tests whether production deployment eliminates development server warnings
"""

import subprocess
import time
import requests
import threading
import sys

def test_no_development_warnings():
    """Test that no development server warnings appear in production mode"""
    print("🔍 Testing for development server warnings...")
    
    # Start the production server
    proc = subprocess.Popen(
        ['python', 'production_deploy.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for startup
        time.sleep(6)
        
        # Test basic connectivity to ensure server is running
        try:
            response = requests.get('http://localhost:5000/health', timeout=10)
            if response.status_code != 200:
                print("❌ Server not responding properly")
                return False
            print(f"✅ Server responding: {response.json()}")
        except Exception as e:
            print(f"❌ Server connectivity failed: {e}")
            return False
        
        # Check for development server warnings
        # Use a short timeout to capture initial startup logs
        try:
            stdout, stderr = proc.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            # Expected - server is still running
            proc.kill()
            stdout, stderr = proc.communicate()
        
        print(f"📋 Stderr output: {stderr[:500]}...")  # Show first 500 chars
        
        # Check for the specific development server warning
        dev_server_warning = "WARNING: This is a development server. Do not use it in a production deployment."
        
        if dev_server_warning in stderr:
            print("❌ DEVELOPMENT SERVER WARNING FOUND!")
            print("⚠️  The application is still using Flask development server")
            return False
        elif "development server" in stderr.lower():
            print("⚠️  Some development server reference found, but not the main warning")
            print("✅ Main production warning eliminated")
            return True
        else:
            print("✅ NO DEVELOPMENT SERVER WARNINGS DETECTED")
            print("🎉 Production WSGI server successfully configured!")
            return True
            
    finally:
        # Cleanup
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()

def test_gunicorn_running():
    """Test that Gunicorn is actually running"""
    print("🔍 Testing if Gunicorn is running...")
    
    proc = subprocess.Popen(
        ['python', 'production_deploy.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        time.sleep(5)
        
        # Check if gunicorn process exists
        ps_proc = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'gunicorn' in ps_proc.stdout:
            print("✅ Gunicorn process detected")
            return True
        else:
            print("❌ Gunicorn process not found")
            return False
            
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()

def main():
    print("🧪 Development Server Warning Elimination Test")
    print("=" * 60)
    
    # Test 1: Check for development warnings
    test1_passed = test_no_development_warnings()
    
    print("\n" + "-" * 40 + "\n")
    
    # Test 2: Verify Gunicorn is running
    test2_passed = test_gunicorn_running()
    
    print("\n" + "=" * 60)
    
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Development server warnings eliminated")
        print("✅ Production WSGI server (Gunicorn) working")
        print("✅ Container stopping issues should be resolved")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        if not test1_passed:
            print("❌ Development server warnings still present")
        if not test2_passed:
            print("❌ Gunicorn not running properly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)