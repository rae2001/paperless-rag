#!/usr/bin/env python3
"""
Simple test script to verify OpenWebUI and RAG API setup
"""

import requests
import time
import sys

def test_service(url, name, timeout=5):
    """Test if a service is accessible"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code in [200, 401, 404]:  # 401 and 404 are OK for some endpoints
            print(f"✅ {name}: Service is running")
            return True
        else:
            print(f"⚠️  {name}: Unexpected response {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Not accessible - {e}")
        return False

def main():
    print("🧪 Testing Paperless RAG Setup")
    print("=" * 40)
    
    services = [
        ("http://localhost:8088/health", "RAG API Health"),
        ("http://localhost:8088", "RAG API"),
        ("http://localhost:3001", "OpenWebUI"),
        ("http://localhost:6333", "Qdrant"),
    ]
    
    results = []
    for url, name in services:
        print(f"\n🔍 Testing {name}...")
        result = test_service(url, name)
        results.append((name, result))
        time.sleep(1)
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    
    all_passed = True
    for name, result in results:
        status = "✅ OK" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All services are running correctly!")
        print("\n📋 Next steps:")
        print("1. Open http://localhost:3001 in your browser")
        print("2. Create an admin account")
        print("3. Add API connection:")
        print("   - Base URL: http://localhost:8088")
        print("   - API Key: dummy-key-not-needed")
        print("4. Start chatting with your documents!")
    else:
        print("⚠️  Some services are not running properly.")
        print("\n🔧 Troubleshooting:")
        print("• Check if containers are running:")
        print("  docker compose -f docker-compose-openwebui.yml ps")
        print("• View logs:")
        print("  docker compose -f docker-compose-openwebui.yml logs")
        print("• Restart services:")
        print("  docker compose -f docker-compose-openwebui.yml restart")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
