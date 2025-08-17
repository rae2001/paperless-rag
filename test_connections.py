#!/usr/bin/env python3
"""
Test connections to Paperless and OpenRouter to help diagnose issues.
"""

import asyncio
import os
import sys
import httpx
from datetime import datetime


def get_env_var(name, default=None):
    """Get environment variable with error handling."""
    value = os.getenv(name, default)
    if not value or value.startswith('your_'):
        return None
    return value


async def test_paperless():
    """Test paperless-ngx connection with various endpoints."""
    print("🔍 Testing Paperless-ngx Connection")
    print("-" * 40)
    
    base_url = get_env_var('PAPERLESS_BASE_URL')
    token = get_env_var('PAPERLESS_API_TOKEN')
    
    if not base_url:
        print("❌ PAPERLESS_BASE_URL not set in .env")
        return False
    
    if not token:
        print("❌ PAPERLESS_API_TOKEN not set in .env")
        return False
    
    print(f"📍 Base URL: {base_url}")
    print(f"🔑 Token: {token[:10]}...{token[-4:] if len(token) > 14 else '***'}")
    
    headers = {"Authorization": f"Token {token}"}
    
    endpoints = [
        ("/api/", "Base API"),
        ("/api/documents/", "Documents list"),
        ("/api/documents/?page_size=1", "Documents with pagination"),
        ("/admin/", "Admin interface"),
        ("/", "Root"),
    ]
    
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        for endpoint, name in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                print(f"\n🔗 Testing {name}: {url}")
                response = await client.get(url, headers=headers)
                
                print(f"   Status: {response.status_code}")
                if response.status_code == 302:
                    location = response.headers.get('location', 'Unknown')
                    print(f"   Redirect to: {location}")
                elif response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        data = response.json()
                        if 'count' in data:
                            print(f"   Documents found: {data['count']}")
                        elif 'results' in data:
                            print(f"   Results: {len(data['results'])} items")
                        else:
                            print(f"   JSON response: {str(data)[:100]}...")
                    else:
                        print(f"   Content-Type: {content_type}")
                        print(f"   Content length: {len(response.content)} bytes")
                elif response.status_code == 401:
                    print("   ❌ Authentication failed - check API token")
                elif response.status_code == 403:
                    print("   ❌ Access forbidden - check token permissions")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # Try a simple connectivity test
    print(f"\n🌐 Testing basic connectivity to {base_url}")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(base_url)
            print(f"   Root responds with: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Paperless server is reachable")
                return True
    except Exception as e:
        print(f"   ❌ Cannot reach paperless server: {e}")
    
    return False


async def test_openrouter():
    """Test OpenRouter connection."""
    print("\n🤖 Testing OpenRouter Connection")
    print("-" * 40)
    
    api_key = get_env_var('OPENROUTER_API_KEY')
    model = get_env_var('OPENROUTER_MODEL', 'openai/gpt-oss-20b')
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set in .env")
        return False
    
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
    print(f"🤖 Model: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test simple completion
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello, respond with just 'OK'"}],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print(f"✅ Success! Response: {content}")
                print(f"Usage: {data.get('usage', {})}")
                return True
            elif response.status_code == 402:
                error_data = response.json()
                print(f"❌ Payment Required: {error_data['error']['message']}")
                print("💳 Add credits at: https://openrouter.ai/settings/credits")
                return False
            elif response.status_code == 401:
                print("❌ Authentication failed - check API key")
                return False
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


def load_env_file():
    """Load .env file if it exists."""
    if os.path.exists('.env'):
        print("📄 Loading .env file...")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    else:
        print("⚠️  No .env file found")
        return False


async def main():
    """Run all connection tests."""
    print("🔧 Paperless RAG Connection Tester")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    load_env_file()
    
    paperless_ok = await test_paperless()
    openrouter_ok = await test_openrouter()
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   Paperless: {'✅ OK' if paperless_ok else '❌ Issues'}")
    print(f"   OpenRouter: {'✅ OK' if openrouter_ok else '❌ Issues'}")
    
    if not paperless_ok:
        print("\n🔧 Paperless Troubleshooting:")
        print("   1. Check if paperless-ngx is running: http://192.168.1.77:8000")
        print("   2. Verify API token in Admin → API Tokens")
        print("   3. Ensure API access is enabled in paperless settings")
        print("   4. Try accessing: http://192.168.1.77:8000/api/documents/")
    
    if not openrouter_ok:
        print("\n💳 OpenRouter Troubleshooting:")
        print("   1. Add credits: https://openrouter.ai/settings/credits")
        print("   2. Check API key: https://openrouter.ai/settings/keys")
        print("   3. Try free models if testing: openai/gpt-oss-20b")
    
    if paperless_ok and openrouter_ok:
        print("\n🎉 All connections working! Your RAG system should work perfectly.")
    
    return paperless_ok and openrouter_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
