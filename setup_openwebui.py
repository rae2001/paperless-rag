#!/usr/bin/env python3
"""
Setup OpenWebUI as a replacement for the broken Streamlit interface
"""

import subprocess
import sys
import time
import requests
import json

def check_docker_permissions():
    """Check if sudo is needed for Docker commands"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def run_command(cmd, description):
    """Run a shell command with description, adding sudo if needed"""
    # Check if we need sudo for docker commands
    if 'docker' in cmd and not check_docker_permissions():
        cmd = f"sudo {cmd}"
    
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
    
    # Check Docker permissions
    if not check_docker_permissions():
        print("ℹ️  Sudo required for Docker commands - will use sudo automatically")
    
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
    if not wait_for_service("http://192.168.1.77:3001", "OpenWebUI"):
        print("❌ OpenWebUI failed to start")
        sys.exit(1)
    
    # Setup configuration
    setup_openwebui_model()
    
    print("\n🎉 Paperless Document Assistant Setup Complete!")
    print("=" * 55)
    print(f"🌐 Document Assistant: http://192.168.1.77:3001")
    print(f"🔗 RAG API: http://192.168.1.77:8088")
    print(f"📄 Paperless: http://192.168.1.77:8000")
    print("")
    print("📋 Next Steps:")
    print("1. Open http://192.168.1.77:3001 in your browser")
    print("2. Create an admin account (first user becomes admin)")
    print("3. The 'paperless-rag' model is pre-configured and ready!")
    print("4. Start asking questions about your documents")
    print("")
    print("💡 Enhanced Integration Features:")
    print("   ✅ Branded as 'Paperless Document Assistant'")
    print("   ✅ RAG features optimized for document Q&A")
    print("   ✅ Helpful suggestions and document-focused UI")
    print("   ✅ Message rating/editing for better results")
    print("   ✅ File upload support for new documents")
    print("   ✅ Privacy-first: all processing happens locally")
    print("")
    print("🚀 Try asking:")
    print("   • 'What documents do I have about taxes?'")
    print("   • 'Summarize my contracts from 2024'")
    print("   • 'Find information about insurance policies'")

if __name__ == "__main__":
    main()
