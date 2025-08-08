#!/usr/bin/env python3
"""
Production Deployment Verification Script
Tests that Ultra-Trader deployment is production-ready without warnings
"""

import subprocess
import time
import requests
import sys
import os

def test_development_server():
    """Test that development server shows warnings"""
    print("🧪 Testing Development Server (should show warnings)...")
    
    # Start development server
    proc = subprocess.Popen(
        ['python', 'optimized_deployment_entry.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, 'PORT': '5002'}
    )
    
    time.sleep(2)
    stdout, stderr = proc.communicate(timeout=5)
    proc.terminate()
    
    output = stdout + stderr
    
    if "WARNING: This is a development server" in output:
        print("✅ Development server correctly shows warnings")
        return True
    else:
        print("❌ Development server warnings not found")
        return False

def test_production_server():
    """Test that production server has no warnings"""
    print("\n🚀 Testing Production Server (should have NO warnings)...")
    
    # Start production server
    proc = subprocess.Popen(
        ['gunicorn', '-c', 'gunicorn.conf.py', 'optimized_deployment_entry:app'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, 'PORT': '5003'}
    )
    
    time.sleep(3)
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:5003/health', timeout=5)
        health_data = response.json()
        
        if health_data.get('deployment') == 'production_ready':
            print("✅ Production server health check passed")
            
            # Test API endpoint
            api_response = requests.get('http://localhost:5003/api/status', timeout=5)
            api_data = api_response.json()
            
            if api_data.get('system') == 'active':
                print("✅ Production API endpoints working")
                
                # Check for absence of development warnings
                proc.terminate()
                stdout, stderr = proc.communicate(timeout=5)
                output = stdout + stderr
                
                if "WARNING: This is a development server" not in output:
                    print("✅ Production server has NO development warnings")
                    return True
                else:
                    print("❌ Production server still shows development warnings")
                    return False
            else:
                print("❌ Production API endpoints failed")
                return False
        else:
            print("❌ Production health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Production server test failed: {e}")
        return False
    finally:
        proc.terminate()

def test_docker_configuration():
    """Verify Docker configuration is production-ready"""
    print("\n🐳 Testing Docker Configuration...")
    
    try:
        # Check Dockerfile uses Gunicorn
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
            
        if 'gunicorn' in dockerfile_content and 'optimized_deployment_entry:app' in dockerfile_content:
            print("✅ Dockerfile configured for production Gunicorn")
            
            # Check Procfile
            with open('Procfile', 'r') as f:
                procfile_content = f.read()
                
            if 'gunicorn' in procfile_content:
                print("✅ Procfile configured for production")
                return True
            else:
                print("❌ Procfile not configured for production")
                return False
        else:
            print("❌ Dockerfile not configured for production")
            return False
            
    except Exception as e:
        print(f"❌ Docker configuration test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Ultra-Trader Production Deployment Verification")
    print("=" * 50)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        test_development_server,
        test_production_server,
        test_docker_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n📊 Verification Results:")
    print("=" * 30)
    
    if all(results):
        print("🎉 ALL TESTS PASSED - Production deployment is ready!")
        print("✅ No development server warnings")
        print("✅ Gunicorn WSGI server working")
        print("✅ Health endpoints functional")
        print("✅ Docker configuration correct")
        return 0
    else:
        print("❌ Some tests failed - production deployment needs attention")
        return 1

if __name__ == '__main__':
    sys.exit(main())