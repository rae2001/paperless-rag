#!/usr/bin/env python3
"""Test if CORS is properly configured after the fix."""

import requests
import sys

def test_cors():
    """Test CORS headers from the API."""
    print("Testing CORS configuration...")
    print("=" * 50)
    
    base_url = "http://localhost:8088"
    
    # Test 1: Basic GET request
    print("\n1. Testing GET /health")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print("   CORS Headers:")
        for header in response.headers:
            if 'access-control' in header.lower():
                print(f"   - {header}: {response.headers[header]}")
        
        if 'access-control-allow-origin' in response.headers:
            print("   ✓ CORS headers present!")
        else:
            print("   ✗ CORS headers MISSING!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: OPTIONS request (preflight)
    print("\n2. Testing OPTIONS /ask (preflight)")
    try:
        response = requests.options(f"{base_url}/ask")
        print(f"   Status: {response.status_code}")
        print("   CORS Headers:")
        for header in response.headers:
            if 'access-control' in header.lower():
                print(f"   - {header}: {response.headers[header]}")
                
        if response.status_code == 200:
            print("   ✓ OPTIONS request handled correctly!")
        else:
            print("   ✗ OPTIONS request failed!")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: POST with Origin header
    print("\n3. Testing POST /ask with Origin header")
    try:
        headers = {
            'Origin': 'http://192.168.1.77:8080',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{base_url}/ask",
            json={"query": "test"},
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        print("   CORS Headers:")
        for header in response.headers:
            if 'access-control' in header.lower():
                print(f"   - {header}: {response.headers[header]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("\nIf CORS headers are still missing, run:")
    print("sudo docker compose down")
    print("sudo docker compose build rag-api --no-cache")
    print("sudo docker compose up -d")

if __name__ == "__main__":
    test_cors()
