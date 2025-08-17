#!/usr/bin/env python3
"""
Complete Paperless RAG + OpenWebUI Integration Setup
This script sets up everything needed for a fully integrated system.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_docker_permissions():
    """Check if sudo is needed for Docker commands"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def run_command(cmd, description, critical=True):
    """Run a shell command with description, adding sudo if needed"""
    if 'docker' in cmd and not check_docker_permissions():
        cmd = f"sudo {cmd}"
    
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
        print("Please copy env.example to .env and configure it first:")
        print("  cp env.example .env")
        print("  # Edit .env with your settings")
        sys.exit(1)
    
    print("✅ Environment file found")

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "openwebui-config"
    ]
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def main():
    print("🚀 Complete Paperless RAG + OpenWebUI Integration Setup")
    print("=" * 70)
    print("This will set up a fully integrated document search system with:")
    print("• RAG API for intelligent document search")
    print("• Qdrant vector database")
    print("• OpenWebUI with custom configuration")
    print("• Automated model and prompt setup")
    print("")
    
    # Preliminary checks
    check_environment()
    create_directories()
    
    if not check_docker_permissions():
        print("ℹ️  Sudo required for Docker commands - will use sudo automatically")
    
    # Step 1: Stop any existing services
    print("\n🛑 Step 1: Stopping existing services")
    run_command("docker compose down", "Stopping main services", critical=False)
    run_command("docker compose -f docker-compose-openwebui.yml down", "Stopping OpenWebUI services", critical=False)
    
    # Step 2: Start core services (RAG API + Qdrant)
    print("\n🔧 Step 2: Starting core services")
    run_command("docker compose up -d qdrant rag-api", "Starting Qdrant and RAG API")
    
    # Wait for services to be ready
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(15)
    
    # Step 3: Start OpenWebUI
    print("\n🌐 Step 3: Starting OpenWebUI")
    run_command("docker compose -f docker-compose-openwebui.yml up -d", "Starting OpenWebUI with custom configuration")
    
    # Wait for OpenWebUI to start
    print("\n⏳ Waiting for OpenWebUI to initialize...")
    time.sleep(20)
    
    # Step 4: Initialize OpenWebUI configuration
    print("\n⚙️  Step 4: Configuring OpenWebUI")
    if Path("initialize_openwebui.py").exists():
        result = subprocess.run([sys.executable, "initialize_openwebui.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ OpenWebUI configuration completed")
        else:
            print("⚠️  OpenWebUI configuration had issues, but continuing...")
            print(f"Details: {result.stderr}")
    else:
        print("⚠️  OpenWebUI initialization script not found, skipping auto-config")
    
    # Step 5: Check service status
    print("\n🔍 Step 5: Checking service status")
    run_command("docker compose -f docker-compose-openwebui.yml ps", "Checking container status", critical=False)
    
    # Final information
    print("\n🎉 Integration Setup Complete!")
    print("=" * 70)
    
    # Service URLs
    print("🌐 Service URLs:")
    print(f"   • OpenWebUI:          http://192.168.1.77:3001")
    print(f"   • RAG API:            http://192.168.1.77:8088")
    print(f"   • RAG API Health:     http://192.168.1.77:8088/health")
    print(f"   • RAG API Docs:       http://192.168.1.77:8088/docs")
    print(f"   • Qdrant Dashboard:   http://192.168.1.77:6333/dashboard")
    print("")
    
    # Access information
    print("🔐 Access Information:")
    print("   • Admin Email:    admin@paperless-rag.local")
    print("   • Admin Password: admin123")
    print("   • Change these credentials after first login!")
    print("")
    
    # Usage instructions
    print("📋 How to use your system:")
    print("1. 🌐 Open http://192.168.1.77:3001 in your browser")
    print("2. 🔐 Login with the admin credentials above")
    print("3. 📝 The model should be auto-configured as 'paperless-rag'")
    print("4. 💬 Start asking questions about your documents!")
    print("")
    
    # Example prompts
    print("💡 Try these example prompts:")
    print("   • 'What documents do I have about taxes?'")
    print("   • 'Find information about insurance policies'")
    print("   • 'Summarize all contracts from 2024'")
    print("   • 'What are the key points in my lease agreement?'")
    print("")
    
    # System prompts
    print("🎯 Available system prompts:")
    print("   • paperless-expert   - Comprehensive document analysis")
    print("   • quick-lookup       - Fast information retrieval")
    print("")
    
    # Troubleshooting
    print("🔧 Troubleshooting:")
    print("   • Check logs:     docker compose -f docker-compose-openwebui.yml logs")
    print("   • Restart all:    docker compose -f docker-compose-openwebui.yml restart")
    print("   • Full reset:     docker compose -f docker-compose-openwebui.yml down && docker volume rm paperless-rag_open-webui-data")
    print("")
    
    # Next steps
    print("📚 Next steps:")
    print("1. Index your documents using the RAG API")
    print("2. Customize system prompts in OpenWebUI settings")
    print("3. Create additional user accounts if needed")
    print("4. Set up document categories and tags")
    
    print("\n✨ Your Paperless RAG system is ready to use!")

if __name__ == "__main__":
    main()
