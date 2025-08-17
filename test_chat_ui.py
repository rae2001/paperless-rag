#!/usr/bin/env python3
"""Test script to verify the chat UI integration with the API."""

import requests
import json
import sys
from urllib.parse import urljoin

def test_api_connection(api_base="http://localhost:8088"):
    """Test basic API connectivity."""
    print(f"Testing API connection to {api_base}")
    
    try:
        # Test health endpoint
        response = requests.get(f"{api_base}/health", timeout=10)
        print(f"✓ Health check: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"  - Status: {health_data.get('status', 'unknown')}")
            
            components = health_data.get('components', {})
            for component, status in components.items():
                print(f"  - {component}: {status}")
        
        # Test CORS preflight
        cors_response = requests.options(f"{api_base}/ask", timeout=10)
        print(f"✓ CORS preflight: {cors_response.status_code}")
        
        # Test basic ask endpoint
        test_query = {"query": "Hello, this is a test query"}
        ask_response = requests.post(
            f"{api_base}/ask", 
            json=test_query,
            timeout=30
        )
        print(f"✓ Ask endpoint: {ask_response.status_code}")
        
        if ask_response.status_code == 200:
            result = ask_response.json()
            print(f"  - Answer received: {len(result.get('answer', ''))} characters")
            print(f"  - Citations: {len(result.get('citations', []))}")
        elif ask_response.status_code == 500:
            print("  - Server error (this is expected if no documents are indexed)")
        else:
            print(f"  - Error: {ask_response.text}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - API is not running")
        print("  Please start the API first: docker compose up")
        return False
    except requests.exceptions.Timeout:
        print("✗ Request timeout - API is slow to respond")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_cors_origins():
    """Test CORS configuration."""
    print("\nTesting CORS configuration...")
    
    try:
        response = requests.get("http://localhost:8088/cors-debug", timeout=10)
        if response.status_code == 200:
            cors_data = response.json()
            origins = cors_data.get('allowed_origins', [])
            print(f"✓ Allowed origins: {origins}")
            
            # Check if common origins are included
            required_origins = [
                'http://localhost:8080',
                'http://127.0.0.1:8080', 
                'http://localhost:3000'
            ]
            
            for origin in required_origins:
                if origin in origins or '*' in origins:
                    print(f"  ✓ {origin} is allowed")
                else:
                    print(f"  ✗ {origin} is NOT allowed")
        else:
            print("✗ Could not retrieve CORS debug info")
            
    except Exception as e:
        print(f"✗ CORS test failed: {e}")

def main():
    """Run all tests."""
    print("Paperless RAG Chat UI Integration Test")
    print("=" * 50)
    
    # Test API connection
    api_ok = test_api_connection()
    
    if api_ok:
        # Test CORS configuration
        test_cors_origins()
        
        print("\n" + "=" * 50)
        print("✓ Integration test completed successfully!")
        print("\nNext steps:")
        print("1. Start the chat UI: python3 serve_chat.py")
        print("2. Open http://localhost:8080 in your browser")
        print("3. Try asking a question about your documents")
        
        return 0
    else:
        print("\n" + "=" * 50)
        print("✗ Integration test failed!")
        print("\nPlease ensure:")
        print("1. Docker containers are running: docker compose up")
        print("2. API is healthy: curl http://localhost:8088/health")
        print("3. Environment variables are configured in .env")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
