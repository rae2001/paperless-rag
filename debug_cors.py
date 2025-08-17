#!/usr/bin/env python3
"""
Debug CORS issues on Ubuntu server.
Run this script to test API connectivity and CORS headers.
"""

import requests
import sys
import subprocess

def test_api_connection():
    """Test API connection and CORS headers."""
    print("CORS Debug Tool for Ubuntu Server")
    print("=" * 50)
    
    # Test URLs
    api_urls = [
        "http://localhost:8088",
        "http://127.0.0.1:8088",
        "http://192.168.1.77:8088"
    ]
    
    for base_url in api_urls:
        print(f"\nTesting {base_url}...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{base_url}/health", timeout=5)
            print(f"✓ Status Code: {response.status_code}")
            
            # Check CORS headers
            headers = response.headers
            cors_headers = {
                'Access-Control-Allow-Origin': headers.get('Access-Control-Allow-Origin', 'MISSING'),
                'Access-Control-Allow-Methods': headers.get('Access-Control-Allow-Methods', 'MISSING'),
                'Access-Control-Allow-Headers': headers.get('Access-Control-Allow-Headers', 'MISSING')
            }
            
            print("\nCORS Headers:")
            for header, value in cors_headers.items():
                status = "✓" if value != "MISSING" else "✗"
                print(f"  {status} {header}: {value}")
            
            # Test OPTIONS request (preflight)
            print("\nTesting OPTIONS (preflight)...")
            options_response = requests.options(f"{base_url}/ask", timeout=5)
            print(f"  OPTIONS Status: {options_response.status_code}")
            
            if response.status_code == 200:
                print(f"\n✓ {base_url} is working!")
                return True
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection failed - API not accessible at {base_url}")
        except requests.exceptions.Timeout:
            print(f"✗ Timeout - API slow to respond at {base_url}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return False

def check_docker_status():
    """Check if Docker containers are running."""
    print("\n" + "=" * 50)
    print("Docker Container Status:")
    try:
        result = subprocess.run(['sudo', 'docker', 'compose', 'ps'], 
                              capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error checking Docker status: {e}")

def main():
    # Check API connection
    api_working = test_api_connection()
    
    # Check Docker status
    check_docker_status()
    
    print("\n" + "=" * 50)
    print("TROUBLESHOOTING STEPS:")
    print()
    
    if not api_working:
        print("1. Restart the API with updated CORS settings:")
        print("   sudo docker compose down")
        print("   sudo docker compose up --build -d")
        print()
        print("2. Check if the API container is running:")
        print("   sudo docker compose ps")
        print()
        print("3. Check API logs for errors:")
        print("   sudo docker compose logs rag-api")
    else:
        print("✓ API is accessible!")
        print()
        print("If you're still seeing CORS errors in the browser:")
        print("1. Clear browser cache and cookies")
        print("2. Try accessing from: http://192.168.1.77:8080")
        print("3. In the UI, click the API URL and set it to: http://192.168.1.77:8088")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
