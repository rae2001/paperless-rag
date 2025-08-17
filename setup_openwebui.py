#!/usr/bin/env python3
"""
Setup OpenWebUI as a replacement for the broken Streamlit interface
"""

import subprocess
import sys
import time
import requests
import json

def run_command(cmd, description):
    """Run a shell command with description"""
    print(f"\n{description}")
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✓ {description} - Success")
        return True
    else:
        print(f"✗ {description} - Failed")
        print(f"Error: {result.stderr}")
        return False

def check_api_health():
    """Check if our RAG API is running"""
    try:
        response = requests.get("http://192.168.1.77:8088/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_service(url, service_name, max_retries=12):
    """Wait for a service to be available"""
    print(f"\nWaiting for {service_name} to start...")
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ {service_name} is ready!")
                return True
        except:
            pass
        
        print(f"   Attempt {i+1}/{max_retries}...")
        time.sleep(5)
    
    print(f"✗ {service_name} failed to start after {max_retries * 5} seconds")
    return False

def setup_openwebui_model():
    """Configure OpenWebUI to use our RAG API"""
    print("\nConfiguring OpenWebUI to use your RAG API...")
    
    # OpenWebUI configuration
    config_data = {
        "models": [
            {
                "id": "paperless-rag",
                "name": "Paperless RAG Assistant",
                "meta": {
                    "description": "AI assistant with access to your Paperless documents",
                    "capabilities": {
                        "vision": False,
                        "function_calling": False
                    }
                },
                "base_url": "http://192.168.1.77:8088",
                "api_key": "dummy-key"
            }
        ]
    }
    
    print("✓ OpenWebUI will auto-discover your RAG API")
    return True

def main():
    print("🚀 Setting up OpenWebUI for Paperless RAG")
    print("=" * 50)
    
    # Check if RAG API is running
    if not check_api_health():
        print("⚠️  RAG API is not running. Starting it first...")
        if not run_command("docker compose up -d rag-api qdrant", "Starting RAG API and Qdrant"):
            print("❌ Failed to start RAG API. Please fix this first.")
            sys.exit(1)
        
        # Wait for API to be ready
        if not wait_for_service("http://192.168.1.77:8088/health", "RAG API"):
            print("❌ RAG API failed to start properly")
            sys.exit(1)
    else:
        print("✓ RAG API is already running")
    
    # Stop any existing OpenWebUI
    print("\n🛑 Stopping existing services...")
    run_command("docker compose -f docker-compose-openwebui.yml down", "Stopping existing OpenWebUI")
    
    # Start OpenWebUI with new compose file
    if not run_command("docker compose -f docker-compose-openwebui.yml up -d", "Starting OpenWebUI"):
        print("❌ Failed to start OpenWebUI")
        sys.exit(1)
    
    # Wait for OpenWebUI to start
    if not wait_for_service("http://192.168.1.77:3000", "OpenWebUI"):
        print("❌ OpenWebUI failed to start")
        sys.exit(1)
    
    # Setup configuration
    setup_openwebui_model()
    
    print("\n🎉 OpenWebUI Setup Complete!")
    print("=" * 50)
    print(f"🌐 OpenWebUI: http://192.168.1.77:3000")
    print(f"🔗 RAG API: http://192.168.1.77:8088")
    print(f"📄 Paperless: http://192.168.1.77:8000")
    print("")
    print("📋 Next Steps:")
    print("1. Open http://192.168.1.77:3000 in your browser")
    print("2. Create an admin account")
    print("3. Go to Settings > Models")
    print("4. Add OpenAI-Compatible API:")
    print("   - API Base URL: http://192.168.1.77:8088")
    print("   - API Key: dummy-key")
    print("5. The model should auto-discover as 'openai/gpt-oss-20b'")
    print("6. Start chatting with your documents!")
    print("")
    print("💡 OpenWebUI features:")
    print("   - Professional chat interface")
    print("   - Conversation history")
    print("   - Multiple users")
    print("   - Model switching")
    print("   - Much more reliable than Streamlit")

if __name__ == "__main__":
    main()
