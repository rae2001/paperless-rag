#!/usr/bin/env python3
"""
Fix and rebuild the RAG API container with proper debugging.
"""

import subprocess
import sys
import os
import time


def detect_docker_compose():
    """Detect whether to use 'docker compose' or 'docker-compose'."""
    try:
        # Try docker compose (newer)
        result = subprocess.run(['docker', 'compose', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'docker compose'
    except:
        pass
    
    try:
        # Try docker-compose (older)
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'docker-compose'
    except:
        pass
    
    return None

def check_docker_permissions():
    """Check if we need sudo for Docker commands."""
    try:
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def run_command(cmd, description, use_sudo=False):
    """Run a command and show output."""
    print(f"\n🔧 {description}")
    
    # Prepare command with sudo if needed
    if use_sudo and not cmd.startswith('sudo'):
        cmd = f"sudo {cmd}"
    
    print(f"Running: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=300
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"💥 {description} failed with error: {e}")
        return False


def check_env_file():
    """Check if .env file exists and has required values."""
    print("\n📋 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("\n📝 Creating .env file from template...")
        
        if os.path.exists('env.example'):
            with open('env.example', 'r') as f:
                content = f.read()
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✅ Created .env file from env.example")
            print("\n⚠️  IMPORTANT: Edit .env file with your actual credentials:")
            print("   - PAPERLESS_API_TOKEN")
            print("   - OPENROUTER_API_KEY")
            return False
        else:
            print("❌ No env.example found either!")
            return False
    
    # Check if required variables are set
    with open('.env', 'r') as f:
        content = f.read()
    
    required_vars = ['PAPERLESS_BASE_URL', 'PAPERLESS_API_TOKEN', 'OPENROUTER_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if f'{var}=your_' in content or f'{var}=' not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ These variables need to be set in .env: {missing_vars}")
        return False
    
    print("✅ .env file looks good")
    return True


def main():
    """Main troubleshooting function."""
    print("🚀 Paperless RAG Container Fix Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print("❌ docker-compose.yml not found. Run this script from the project root.")
        sys.exit(1)
    
    # Detect Docker setup
    compose_cmd = detect_docker_compose()
    if not compose_cmd:
        print("❌ Neither 'docker compose' nor 'docker-compose' found!")
        print("Please install Docker and Docker Compose.")
        sys.exit(1)
    
    print(f"✅ Found Docker Compose: {compose_cmd}")
    
    # Check Docker permissions
    need_sudo = not check_docker_permissions()
    if need_sudo:
        print("⚠️  Docker needs sudo permissions")
        print("💡 Tip: Add your user to the docker group to avoid sudo:")
        print("   sudo usermod -aG docker $USER")
        print("   Then log out and back in")
    else:
        print("✅ Docker permissions OK")
    
    # Check .env file
    env_ok = check_env_file()
    if not env_ok:
        print("\n⚠️  Please edit .env file with your credentials before continuing.")
        print("Press Enter when ready to continue...")
        input()
    
    # Stop any running containers
    if not run_command(f"{compose_cmd} down", "Stopping existing containers", need_sudo):
        print("⚠️  Could not stop containers, continuing anyway...")
    
    # Remove old images to force rebuild
    if not run_command(f"{compose_cmd} down --rmi all", "Removing old images", need_sudo):
        print("⚠️  Could not remove images, continuing anyway...")
    
    # Clean up containers and volumes
    if not run_command("docker system prune -f", "Cleaning up Docker system", need_sudo):
        print("⚠️  Could not clean up, continuing anyway...")
    
    # Build the image
    if not run_command(f"{compose_cmd} build --no-cache --pull rag-api", "Building RAG API image", need_sudo):
        print("❌ Build failed!")
        return False
    
    # Start the services
    if not run_command(f"{compose_cmd} up -d", "Starting services", need_sudo):
        print("❌ Failed to start services!")
        return False
    
    # Wait a bit for startup
    print("\n⏳ Waiting for services to start...")
    time.sleep(10)
    
    # Check status
    if not run_command(f"{compose_cmd} ps", "Checking service status", need_sudo):
        print("❌ Could not check status!")
        return False
    
    # Check logs
    print("\n📝 Recent logs from rag-api:")
    run_command(f"{compose_cmd} logs --tail=20 rag-api", "Checking recent logs", need_sudo)
    
    # Test health
    print("\n🏥 Testing health endpoint...")
    time.sleep(5)  # Give it a moment more
    
    try:
        import requests
        response = requests.get("http://localhost:8088/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed!")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("\n📋 Full logs:")
        run_command(f"{compose_cmd} logs rag-api", "Getting full logs", need_sudo)
        return False
    
    print("\n🎉 Container fixed and running!")
    print("\nNext steps:")
    print("1. Test with: python3 test_api.py")
    print("2. Ingest documents: curl -X POST http://localhost:8088/ingest -H 'Content-Type: application/json' -d '{}'")
    print("3. Ask questions: curl -X POST http://localhost:8088/ask -H 'Content-Type: application/json' -d '{\"query\": \"test\"}'")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
