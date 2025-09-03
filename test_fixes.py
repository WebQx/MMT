#!/usr/bin/env python3
"""Test script for production fixes."""

import requests
import json
import time
import subprocess
import sys

BASE_URL = "http://localhost:9000"

def test_security_fixes():
    """Test security vulnerability fixes."""
    print("🔒 Testing security fixes...")
    
    # Test path traversal fix
    try:
        resp = requests.post(f"{BASE_URL}/upload_chunk/", 
                           files={"chunk": ("../../../etc/passwd", b"test")},
                           data={"filename": "../../../etc/passwd"})
        assert resp.status_code == 400, "Path traversal should be blocked"
        print("✅ Path traversal protection working")
    except Exception as e:
        print(f"❌ Path traversal test failed: {e}")

def test_error_handling():
    """Test improved error handling."""
    print("🔧 Testing error handling...")
    
    # Test invalid JSON
    try:
        resp = requests.post(f"{BASE_URL}/transcribe/cloud/", 
                           json="invalid json")
        assert resp.status_code == 400
        print("✅ Invalid JSON handled properly")
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

def test_input_validation():
    """Test input validation."""
    print("📝 Testing input validation...")
    
    # Test empty filename
    try:
        resp = requests.post(f"{BASE_URL}/upload_chunk/",
                           files={"chunk": ("", b"test")},
                           data={"filename": ""})
        assert resp.status_code == 400
        print("✅ Empty filename validation working")
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")

def test_health_endpoints():
    """Test health endpoints."""
    print("🏥 Testing health endpoints...")
    
    try:
        resp = requests.get(f"{BASE_URL}/healthz")
        assert resp.status_code == 200
        print("✅ Health endpoint working")
        
        resp = requests.get(f"{BASE_URL}/metrics")
        assert resp.status_code == 200
        print("✅ Metrics endpoint working")
    except Exception as e:
        print(f"❌ Health test failed: {e}")

def run_backend_tests():
    """Run backend test suite."""
    print("🧪 Running backend tests...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "backend/tests/", "-v", "--tb=short"],
            cwd=".",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ All backend tests passed")
        else:
            print(f"❌ Some tests failed:\n{result.stdout}\n{result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

def main():
    print("🚀 Testing MMT Production Fixes\n")
    
    # Check if backend is running
    try:
        resp = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if resp.status_code != 200:
            print("❌ Backend not healthy. Start with: uvicorn main:app --reload --port 9000")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running. Start with: uvicorn main:app --reload --port 9000")
        return
    
    print("✅ Backend is running\n")
    
    # Run tests
    test_health_endpoints()
    test_security_fixes()
    test_error_handling()
    test_input_validation()
    run_backend_tests()
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    main()