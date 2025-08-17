#!/usr/bin/env python3
"""
Quick rebuild script to fix the torch version issue.
"""

import subprocess
import sys
import os


def detect_docker_compose():
    """Detect whether to use 'docker compose' or 'docker-compose'."""
    try:
        result = subprocess.run(['docker', 'compose', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return 'docker compose'
    except:
        pass
    
    try:
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


def run_command(cmd, need_sudo=False):
    """Run a command with proper sudo handling."""
    if need_sudo and not cmd.startswith('sudo'):
        cmd = f"sudo {cmd}"
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    print("🔧 Quick Rebuild for Torch Version Fix")
    print("=" * 40)
    
    if not os.path.exists('docker-compose.yml'):
        print("❌ docker-compose.yml not found. Run from project root.")
        sys.exit(1)
    
    # Detect setup
    compose_cmd = detect_docker_compose()
    if not compose_cmd:
        print("❌ Docker Compose not found!")
        sys.exit(1)
    
    need_sudo = not check_docker_permissions()
    sudo_prefix = "sudo " if need_sudo else ""
    
    print(f"✅ Using: {compose_cmd}")
    if need_sudo:
        print("⚠️  Using sudo for Docker commands")
    
    print("\n🛑 Stopping containers...")
    run_command(f"{compose_cmd} down", need_sudo)
    
    print("\n🗑️  Removing old rag-api image...")
    run_command(f"{compose_cmd} down --rmi local", need_sudo)
    
    print("\n🔨 Building with updated torch version...")
    success = run_command(f"{compose_cmd} build --no-cache rag-api", need_sudo)
    
    if not success:
        print("❌ Build failed! Check the output above.")
        print("\n💡 Manual commands:")
        print(f"   {sudo_prefix}{compose_cmd} down")
        print(f"   {sudo_prefix}{compose_cmd} build --no-cache rag-api")
        print(f"   {sudo_prefix}{compose_cmd} up -d")
        sys.exit(1)
    
    print("\n🚀 Starting services...")
    success = run_command(f"{compose_cmd} up -d", need_sudo)
    
    if not success:
        print("❌ Failed to start services!")
        sys.exit(1)
    
    print("\n⏳ Waiting for startup...")
    import time
    time.sleep(10)
    
    print("\n📋 Checking status...")
    run_command(f"{compose_cmd} ps", need_sudo)
    
    print("\n📝 Recent logs...")
    run_command(f"{compose_cmd} logs --tail=10 rag-api", need_sudo)
    
    print("\n🎉 Rebuild complete!")
    print("\n🧪 Test the API:")
    print("   curl http://localhost:8088/health")
    print("   python3 test_api.py")


if __name__ == "__main__":
    main()
