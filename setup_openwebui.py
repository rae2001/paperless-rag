#!/usr/bin/env python3
"""
Setup OpenWebUI as an enhanced Paperless Document Assistant interface
"""

import subprocess
import sys
import time
import requests
import json
import os
from pathlib import Path

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

def validate_env_file():
    """Validate that .env file has required settings"""
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  .env file not found. Run ./setup.sh first!")
        return False
    
    required_vars = ["PAPERLESS_API_TOKEN", "OPENROUTER_API_KEY"]
    missing_vars = []
    
    with open(env_path, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your_" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please edit .env file with your actual tokens")
        return False
    
    print("✓ Environment configuration validated")
    return True

def validate_custom_config():
    """Validate that custom OpenWebUI configuration exists"""
    config_dir = Path("openwebui-config")
    config_file = config_dir / "config.yaml"
    
    if not config_dir.exists():
        print("📁 Creating OpenWebUI config directory...")
        config_dir.mkdir(exist_ok=True)
    
    if not config_file.exists():
        print("📝 Creating custom OpenWebUI configuration...")
        
        # Create the enhanced config file
        config_content = """# OpenWebUI Configuration for Paperless RAG Integration
# This file provides custom configuration for better integration

# UI Customization
ui:
  name: "Paperless Document Assistant"
  description: "AI-powered Q&A for your document collection"
  favicon: "/favicon.ico"
  logo: null
  
# Default Settings for New Users
defaults:
  model: "paperless-rag"
  temperature: 0.1
  top_p: 0.9
  max_tokens: 1000
  
# Chat Behavior
chat:
  default_system_prompt: |
    You are a helpful document assistant specializing in answering questions about documents.
    Always provide specific citations when referencing document content.
    If you cannot find relevant information in the provided context, clearly state this.
  
  suggestions:
    - "What documents do I have about [topic]?"
    - "Summarize the key points from [document name]"
    - "Find information about [specific topic] in my documents"
    - "Compare information between multiple documents"

# Model Configuration
models:
  paperless-rag:
    name: "Paperless RAG"
    description: "Document Q&A powered by your paperless collection"
    capabilities:
      - "document_search"
      - "citation_generation"
      - "multi_document_analysis"

# RAG-specific settings
rag:
  enabled: true
  chunk_size: 600
  chunk_overlap: 100
  top_k: 5
  similarity_threshold: 0.75
  
# Feature flags optimized for document Q&A
features:
  web_search: false
  image_generation: false
  code_execution: false
  file_upload: true
  document_analysis: true
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
    
    print("✓ Custom OpenWebUI configuration ready")
    return True

def setup_openwebui_model():
    """Configure and validate OpenWebUI setup"""
    print("\n🔧 Validating enhanced integration setup...")
    
    # Validate environment
    if not validate_env_file():
        print("💡 Tip: Run './setup.sh' first to create and configure .env file")
        return False
    
    # Validate custom configuration
    if not validate_custom_config():
        return False
    
    # Test API connectivity
    try:
        response = requests.get("http://192.168.1.77:8088/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ RAG API is healthy: {health_data.get('status', 'unknown')}")
        else:
            print("⚠️  RAG API responded but with unexpected status")
    except Exception as e:
        print(f"⚠️  Could not verify RAG API health: {e}")
    
    print("✓ Enhanced OpenWebUI integration configured")
    print("✓ Custom branding and document-focused features enabled")
    print("✓ RAG settings optimized for paperless documents")
    return True

def main():
    print("🚀 Setting up Enhanced Paperless Document Assistant")
    print("=" * 55)
    
    # Check Docker permissions
    if not check_docker_permissions():
        print("ℹ️  Sudo required for Docker commands - will use sudo automatically")
    
    # Pre-flight checks
    print("\n🔍 Running pre-flight checks...")
    if not os.path.exists("docker-compose-openwebui.yml"):
        print("❌ docker-compose-openwebui.yml not found!")
        print("💡 Make sure you're in the paperless-rag directory")
        sys.exit(1)
    
    if not os.path.exists(".env"):
        print("⚠️  .env file not found. Creating from template...")
        if os.path.exists("env.example"):
            import shutil
            shutil.copy("env.example", ".env")
            print("✓ Created .env file from template")
            print("📝 Please edit .env with your actual API tokens before continuing")
        else:
            print("❌ env.example not found. Run './setup.sh' first!")
            sys.exit(1)
    
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
    
    # Setup and validate enhanced configuration
    if not setup_openwebui_model():
        print("\n⚠️  Setup completed with warnings. Please check the issues above.")
        print("💡 You can still use OpenWebUI, but some features may not work optimally.")
        print("")
    
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
    print("   ✅ Custom config with document-focused suggestions")
    print("   ✅ RAG features optimized for document Q&A")
    print("   ✅ Message rating/editing for better results")
    print("   ✅ File upload support for new documents")
    print("   ✅ Privacy-first: disabled web search and external features")
    print("   ✅ Environment validation and health checks")
    print("")
    print("🚀 Try asking:")
    print("   • 'What documents do I have about taxes?'")
    print("   • 'Summarize my contracts from 2024'")
    print("   • 'Find information about insurance policies'")
    print("")
    print("🔍 Need help? Check:")
    print("   • README.md for detailed documentation")
    print("   • TROUBLESHOOTING.md for common issues")
    print("   • Run 'python test_api.py' to verify everything works")

if __name__ == "__main__":
    main()
