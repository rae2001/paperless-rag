#!/usr/bin/env python3
"""
Show manual commands to fix the Docker setup.
This helps when the automated script has issues.
"""

import subprocess
import sys
import os


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


def main():
    print("🔧 Manual Docker Fix Commands")
    print("=" * 40)
    
    # Detect setup
    compose_cmd = detect_docker_compose()
    if not compose_cmd:
        print("❌ Docker Compose not found!")
        print("\nInstall Docker Compose:")
        print("# For Ubuntu/Debian:")
        print("sudo apt update")
        print("sudo apt install docker.io docker-compose-plugin")
        print("\n# Or install Docker Desktop which includes Compose")
        return
    
    print(f"✅ Found: {compose_cmd}")
    
    need_sudo = not check_docker_permissions()
    sudo_prefix = "sudo " if need_sudo else ""
    
    if need_sudo:
        print("⚠️  Requires sudo")
        print("\n💡 To avoid sudo in future:")
        print("sudo usermod -aG docker $USER")
        print("# Then log out and back in")
    
    print(f"\n📋 Run these commands in order:")
    print(f"# 1. Stop existing containers")
    print(f"{sudo_prefix}{compose_cmd} down")
    
    print(f"\n# 2. Remove old images (force rebuild)")
    print(f"{sudo_prefix}{compose_cmd} down --rmi all")
    
    print(f"\n# 3. Clean up Docker system")
    print(f"{sudo_prefix}docker system prune -f")
    
    print(f"\n# 4. Build fresh image")
    print(f"{sudo_prefix}{compose_cmd} build --no-cache --pull rag-api")
    
    print(f"\n# 5. Start services")
    print(f"{sudo_prefix}{compose_cmd} up -d")
    
    print(f"\n# 6. Check status")
    print(f"{sudo_prefix}{compose_cmd} ps")
    print(f"{sudo_prefix}{compose_cmd} logs --tail=20 rag-api")
    
    print(f"\n# 7. Test health")
    print("curl http://localhost:8088/health")
    
    print("\n🔍 Troubleshooting:")
    print(f"# View all logs: {sudo_prefix}{compose_cmd} logs rag-api")
    print(f"# Restart service: {sudo_prefix}{compose_cmd} restart rag-api")
    print(f"# Enter container: {sudo_prefix}docker exec -it rag-api bash")
    
    if not os.path.exists('.env'):
        print("\n⚠️  Don't forget to create .env file first:")
        print("python3 create_env.py")
        print("# Then edit with your actual tokens")


if __name__ == "__main__":
    main()
