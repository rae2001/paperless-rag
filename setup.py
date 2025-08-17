#!/usr/bin/env python3
"""
Simplified Paperless RAG + OpenWebUI Setup
This script provides a streamlined setup for the integrated system.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_docker_permissions():
    """Check if Docker is accessible without sudo"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def run_command(cmd, description, critical=True):
    """Run a shell command with description"""
    # No need for replacement - commands already use modern docker compose syntax
    
    print(f"\n🔄 {description}")
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - Success")
        return True
    else:
        print(f"❌ {description} - Failed")
        if result.stderr:
            print(f"Error: {result.stderr}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        
        if critical:
            print("This is a critical step. Cannot continue.")
            sys.exit(1)
        return False

def check_environment():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("Creating .env from template...")
        if Path("env.example").exists():
            subprocess.run(['copy' if os.name == 'nt' else 'cp', 'env.example', '.env'], shell=True)
            print("✅ Created .env file from template")
            print("")
            print("⚠️  IMPORTANT: Edit .env with your actual credentials:")
            print("   - PAPERLESS_API_TOKEN: Get from your paperless-ngx settings")
            print("   - OPENROUTER_API_KEY: Get from https://openrouter.ai/")
            print("")
            return False
        else:
            print("❌ env.example not found!")
            sys.exit(1)
    
    print("✅ Environment file found")
    return True

def create_directories():
    """Create necessary directories"""
    directories = ["logs", "openwebui-config"]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def main():
    print("🚀 Paperless RAG + OpenWebUI Setup")
    print("=" * 50)
    print("This will set up:")
    print("• RAG API for intelligent document search")
    print("• Qdrant vector database")
    print("• OpenWebUI with simplified configuration")
    print("")
    
    # Preliminary checks
    env_ready = check_environment()
    create_directories()
    
    if not env_ready:
        print("Please edit your .env file and run this script again.")
        sys.exit(0)
    
    # Stop any existing services
    print("\n🛑 Stopping existing services")
    run_command("docker compose down", "Stopping main services", critical=False)
    run_command("docker compose -f docker-compose-openwebui.yml down", "Stopping OpenWebUI services", critical=False)
    
    # Start services
    print("\n🔧 Starting all services")
    run_command("docker compose -f docker-compose-openwebui.yml up -d", "Starting integrated system")
    
    # Wait for services to be ready
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(30)
    
    # Check service status
    print("\n🔍 Checking service status")
    run_command("docker compose -f docker-compose-openwebui.yml ps", "Checking container status", critical=False)
    
    # Final information
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    
    print("🌐 Service URLs:")
    print("   • OpenWebUI:          http://localhost:3001")
    print("   • RAG API:            http://localhost:8088")
    print("   • RAG API Health:     http://localhost:8088/health")
    print("   • Qdrant Dashboard:   http://localhost:6333/dashboard")
    print("")
    
    print("📋 Next Steps:")
    print("1. 🌐 Open http://localhost:3001 in your browser")
    print("2. 👤 Create an admin account")
    print("3. ⚙️  Go to Settings > Connections")
    print("4. 🔗 Add OpenAI API Connection:")
    print("   - Base URL: http://localhost:8088")
    print("   - API Key: dummy-key-not-needed")
    print("5. 💬 Start asking questions about your documents!")
    print("")
    
    print("🔧 Troubleshooting:")
    print("   • View logs: docker compose -f docker-compose-openwebui.yml logs")
    print("   • Restart:   docker compose -f docker-compose-openwebui.yml restart")
    print("   • Stop:      docker compose -f docker-compose-openwebui.yml down")
    print("")
    
    print("✨ Your Paperless RAG system is ready!")

if __name__ == "__main__":
    main()
