#!/usr/bin/env python3
"""
Basic test script to verify the MMT backend functionality
"""

import requests
import json
import sys
from pathlib import Path

def test_backend():
    """Test the MMT backend API endpoints"""
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 8000")
        return False
    
    # Test guest login
    print("\nTesting guest login...")
    try:
        response = requests.post("http://localhost:8000/login/guest")
        if response.status_code == 200:
            auth_data = response.json()
            access_token = auth_data.get('access_token')
            print("✅ Guest login working")
            print(f"Token received: {access_token[:20]}...")
            
            # Test authenticated endpoint
            print("\nTesting authenticated endpoint...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get("http://localhost:8000/health", headers=headers)
            if response.status_code == 200:
                print("✅ Authentication working")
                print(f"Health check: {response.json()}")
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        else:
            print(f"❌ Guest login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Guest login error: {e}")
        return False
    
    print("\n🎉 All basic tests passed!")
    return True

if __name__ == "__main__":
    print("MMT Backend Test Suite")
    print("=" * 30)
    
    if test_backend():
        print("\n✅ Backend is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Backend tests failed!")
        sys.exit(1)