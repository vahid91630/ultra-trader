#!/usr/bin/env python3
"""
Deployment Fixes Verification Script
Tests all the deployed fixes to ensure they work correctly
"""

import subprocess
import time
import json
import requests
import sys

def run_command(cmd, capture_output=True, text=True, timeout=30):
    """Run a command safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, 
                              text=text, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_docker_build():
    """Test Docker build process"""
    print("🔨 Testing Docker build...")
    success, stdout, stderr = run_command("docker build -t ultra-trader-test .", timeout=300)
    
    if success:
        print("✅ Docker build successful")
        return True
    else:
        print(f"❌ Docker build failed: {stderr}")
        return False

def test_gunicorn_deployment():
    """Test Gunicorn deployment"""
    print("🚀 Testing Gunicorn deployment...")
    
    # Start gunicorn in background
    process = subprocess.Popen([
        "gunicorn", "--bind", "0.0.0.0:5001", "--workers", "1", 
        "--timeout", "120", "optimized_deployment_entry:app"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(3)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:5001/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy" and data.get("server") == "gunicorn_wsgi":
                print("✅ Gunicorn deployment successful")
                print(f"   Health check: {data}")
                return True
            else:
                print("❌ Health check failed")
                return False
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to Gunicorn: {e}")
        return False
    finally:
        # Cleanup
        process.terminate()
        process.wait()

def test_container_deployment():
    """Test full container deployment"""
    print("🐳 Testing container deployment...")
    
    # Stop any existing test containers
    run_command("docker stop ultra-trader-test-verify 2>/dev/null", capture_output=False)
    run_command("docker rm ultra-trader-test-verify 2>/dev/null", capture_output=False)
    
    # Start container
    success, stdout, stderr = run_command(
        "docker run -d --name ultra-trader-test-verify -p 5002:5000 ultra-trader-test"
    )
    
    if not success:
        print(f"❌ Failed to start container: {stderr}")
        return False
    
    # Wait for startup
    time.sleep(5)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:5002/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Container deployment successful")
                print(f"   Container health: {data}")
                
                # Test status endpoint too
                status_response = requests.get("http://localhost:5002/api/status", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   API status: {status_data}")
                
                return True
            else:
                print("❌ Container health check failed")
                return False
        else:
            print(f"❌ Container health endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to connect to container: {e}")
        return False
    finally:
        # Cleanup
        run_command("docker stop ultra-trader-test-verify", capture_output=False)
        run_command("docker rm ultra-trader-test-verify", capture_output=False)

def test_signal_handling():
    """Test graceful shutdown and signal handling"""
    print("🛑 Testing signal handling...")
    
    # Start process
    process = subprocess.Popen([
        "python3", "optimized_deployment_entry.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={"PORT": "5003"})
    
    # Wait for startup
    time.sleep(2)
    
    try:
        # Send SIGTERM
        process.terminate()
        process.wait(timeout=5)
        
        if process.returncode == 0:
            print("✅ Graceful shutdown successful")
            return True
        else:
            print("❌ Process did not shut down gracefully")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Process did not respond to SIGTERM")
        process.kill()
        return False

def test_ssl_fix():
    """Test SSL certificate fix in requirements installation"""
    print("🔐 Testing SSL certificate fix...")
    
    # Test pip install with trusted hosts
    success, stdout, stderr = run_command(
        "pip install --dry-run --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org flask==3.1.1"
    )
    
    if success:
        print("✅ SSL certificate fix working")
        return True
    else:
        print(f"❌ SSL fix failed: {stderr}")
        return False

def main():
    """Run all verification tests"""
    print("🧪 Starting Ultra-Trader Deployment Fixes Verification")
    print("=" * 60)
    
    tests = [
        ("SSL Certificate Fix", test_ssl_fix),
        ("Docker Build", test_docker_build),
        ("Gunicorn Deployment", test_gunicorn_deployment),
        ("Signal Handling", test_signal_handling),
        ("Container Deployment", test_container_deployment),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All deployment fixes verified successfully!")
        
        # Save verification results
        verification_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total,
            "passed_tests": passed,
            "test_results": results,
            "status": "ALL_FIXES_VERIFIED"
        }
        
        with open("deployment_fixes_verification.json", "w") as f:
            json.dump(verification_data, f, indent=2)
            
        print("📝 Verification results saved to deployment_fixes_verification.json")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()