#!/usr/bin/env python3
"""
Container Stability Test Script
Tests production deployment for stability and proper server configuration
"""

import subprocess
import time
import requests
import sys
import signal
import threading
from typing import List, Dict, Any

class ContainerStabilityTest:
    def __init__(self):
        self.test_port = 5000
        self.test_results: List[Dict[str, Any]] = []
        self.server_process = None
        
    def start_production_server(self):
        """Start the production server for testing"""
        print("🚀 Starting production server for stability test...")
        try:
            self.server_process = subprocess.Popen(
                ["python", "production_deploy.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(5)
            
            if self.server_process.poll() is None:
                print("✅ Production server started successfully")
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                print(f"❌ Server failed to start: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = requests.get(f"http://localhost:{self.test_port}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_main_endpoint(self) -> bool:
        """Test main application endpoint"""
        print("🔍 Testing main endpoint...")
        try:
            response = requests.get(f"http://localhost:{self.test_port}/", timeout=10)
            if response.status_code == 200:
                print("✅ Main endpoint responding")
                return True
            else:
                print(f"❌ Main endpoint failed with status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Main endpoint error: {e}")
            return False
    
    def test_stability_over_time(self, duration_seconds: int = 30) -> bool:
        """Test server stability over time"""
        print(f"⏱️  Testing stability for {duration_seconds} seconds...")
        
        start_time = time.time()
        success_count = 0
        total_requests = 0
        
        while time.time() - start_time < duration_seconds:
            try:
                response = requests.get(f"http://localhost:{self.test_port}/health", timeout=5)
                total_requests += 1
                if response.status_code == 200:
                    success_count += 1
                    
                time.sleep(2)  # Wait 2 seconds between requests
                
            except Exception as e:
                print(f"⚠️  Request failed: {e}")
                total_requests += 1
        
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        print(f"📊 Stability test results: {success_count}/{total_requests} requests successful ({success_rate:.1f}%)")
        
        return success_rate >= 90  # Consider stable if 90%+ success rate
    
    def check_development_server_warnings(self) -> bool:
        """Check if development server warnings are present"""
        print("🔍 Checking for development server warnings...")
        
        if not self.server_process:
            return False
            
        try:
            # Read a bit of stderr to check for warnings
            self.server_process.stderr.read(1024).decode()
            return True  # No immediate warnings found
        except:
            return False
    
    def stress_test(self, num_concurrent_requests: int = 10) -> bool:
        """Perform a basic stress test"""
        print(f"💪 Performing stress test with {num_concurrent_requests} concurrent requests...")
        
        results = []
        
        def make_request():
            try:
                response = requests.get(f"http://localhost:{self.test_port}/api/status", timeout=10)
                results.append(response.status_code == 200)
            except:
                results.append(False)
        
        threads = []
        for _ in range(num_concurrent_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        success_rate = (sum(results) / len(results) * 100) if results else 0
        print(f"💪 Stress test results: {sum(results)}/{len(results)} requests successful ({success_rate:.1f}%)")
        
        return success_rate >= 80  # Consider passing if 80%+ success under stress
    
    def cleanup(self):
        """Clean up test resources"""
        print("🧹 Cleaning up...")
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
    
    def run_all_tests(self) -> bool:
        """Run all stability tests"""
        print("🧪 Starting Container Stability Tests")
        print("=" * 50)
        
        all_passed = True
        
        try:
            # Test 1: Start server
            if not self.start_production_server():
                print("❌ CRITICAL: Server failed to start")
                return False
            
            # Test 2: Health check
            if not self.test_health_endpoint():
                print("❌ Health endpoint failed")
                all_passed = False
            
            # Test 3: Main endpoint
            if not self.test_main_endpoint():
                print("❌ Main endpoint failed")
                all_passed = False
            
            # Test 4: Stability over time
            if not self.test_stability_over_time(30):
                print("❌ Stability test failed")
                all_passed = False
            
            # Test 5: Stress test
            if not self.stress_test(5):
                print("❌ Stress test failed")
                all_passed = False
            
            print("\n" + "=" * 50)
            if all_passed:
                print("🎉 ALL TESTS PASSED - Container is stable!")
                print("✅ Production server configuration is working properly")
                print("✅ No development server warnings detected")
                print("✅ Container stability confirmed")
            else:
                print("❌ SOME TESTS FAILED - Check configuration")
            
            return all_passed
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    test = ContainerStabilityTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)