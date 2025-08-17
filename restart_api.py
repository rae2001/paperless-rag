#!/usr/bin/env python3
"""
Quick restart of the rag-api service to apply connection fixes.
"""

import subprocess
import sys
import time


def detect_docker_compose():
    """Detect docker compose command."""
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
    """Check if sudo is needed."""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False


def run_cmd(cmd, need_sudo=False):
    """Run command with sudo if needed."""
    if need_sudo and not cmd.startswith('sudo'):
        cmd = f"sudo {cmd}"
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    print("🔄 Quick Restart RAG API (with ingestion fixes)")
    print("=" * 45)
    
    compose_cmd = detect_docker_compose()
    if not compose_cmd:
        print("❌ Docker Compose not found!")
        sys.exit(1)
    
    need_sudo = not check_docker_permissions()
    
    print("🛑 Stopping rag-api...")
    run_cmd(f"{compose_cmd} stop rag-api", need_sudo)
    
    print("🔨 Rebuilding rag-api (quick build)...")
    success = run_cmd(f"{compose_cmd} build rag-api", need_sudo)
    
    if not success:
        print("❌ Build failed!")
        sys.exit(1)
    
    print("🚀 Starting rag-api...")
    run_cmd(f"{compose_cmd} up -d rag-api", need_sudo)
    
    print("⏳ Waiting for startup...")
    time.sleep(8)
    
    print("📝 Checking logs...")
    run_cmd(f"{compose_cmd} logs --tail=10 rag-api", need_sudo)
    
    print("\n🧪 Test the API:")
    print("   curl http://localhost:8088/health")
    print("   python3 test_connections.py")


if __name__ == "__main__":
    main()
