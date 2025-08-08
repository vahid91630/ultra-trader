#!/usr/bin/env python3
"""
Railway Deployment Test Script
Tests the deployment configuration locally
"""

import os
import subprocess
import time
import requests
import sys

def test_deployment():
    """Test the Railway deployment configuration"""
    print("🧪 Testing Railway deployment configuration...")
    
    # Test 1: Check if required files exist
    required_files = ['Procfile', 'requirements.txt', 'optimized_deployment_entry.py', 'Dockerfile']
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    # Test 2: Check Procfile content
    with open('Procfile', 'r') as f:
        procfile_content = f.read().strip()
    
    if 'gunicorn optimized_deployment_entry:app' in procfile_content:
        print("✅ Procfile configured for Flask app with gunicorn")
    else:
        print("❌ Procfile not configured correctly")
        return False
    
    # Test 3: Check requirements.txt has necessary dependencies
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    required_deps = ['flask', 'gunicorn']
    for dep in required_deps:
        if dep in requirements.lower():
            print(f"✅ {dep} found in requirements.txt")
        else:
            print(f"❌ {dep} missing from requirements.txt")
            return False
    
    print("\n🎉 All deployment configuration tests passed!")
    print("🚀 Ready for Railway deployment!")
    
    return True

if __name__ == "__main__":
    success = test_deployment()
    sys.exit(0 if success else 1)