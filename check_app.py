#!/usr/bin/env python3
"""
Quick check to see what application is actually running in the container.
"""

import subprocess
import json


def check_container():
    """Check what's running in the rag-api container."""
    
    print("🔍 Checking what's actually running in the container...")
    
    # Check if container is running
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=rag-api", "--format", "json"],
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            print("❌ Docker command failed")
            return
        
        if not result.stdout.strip():
            print("❌ No rag-api container running")
            return
        
        print("✅ rag-api container is running")
        
        # Check the file structure inside container
        print("\n📁 Checking file structure in container:")
        exec_result = subprocess.run(
            ["docker", "exec", "rag-api", "find", "/app", "-name", "*.py"],
            capture_output=True,
            text=True
        )
        
        if exec_result.returncode == 0:
            print("Python files in container:")
            for line in exec_result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("❌ Could not list files in container")
        
        # Check what process is running
        print("\n⚙️  Checking running processes:")
        ps_result = subprocess.run(
            ["docker", "exec", "rag-api", "ps", "aux"],
            capture_output=True,
            text=True
        )
        
        if ps_result.returncode == 0:
            print("Running processes:")
            for line in ps_result.stdout.strip().split('\n'):
                if 'python' in line or 'uvicorn' in line:
                    print(f"   {line}")
        
        # Check environment variables
        print("\n🌍 Checking environment variables:")
        env_result = subprocess.run(
            ["docker", "exec", "rag-api", "env"],
            capture_output=True,
            text=True
        )
        
        if env_result.returncode == 0:
            env_vars = env_result.stdout.strip().split('\n')
            relevant_vars = [var for var in env_vars if any(key in var for key in ['PAPERLESS', 'OPENROUTER', 'QDRANT'])]
            
            if relevant_vars:
                print("Relevant environment variables:")
                for var in relevant_vars:
                    # Hide sensitive values
                    if 'TOKEN' in var or 'KEY' in var:
                        name = var.split('=')[0]
                        print(f"   {name}=***hidden***")
                    else:
                        print(f"   {var}")
            else:
                print("❌ No relevant environment variables found!")
        
        # Try to get logs
        print("\n📋 Recent container logs:")
        logs_result = subprocess.run(
            ["docker", "logs", "--tail", "10", "rag-api"],
            capture_output=True,
            text=True
        )
        
        if logs_result.returncode == 0:
            print("Recent logs:")
            for line in logs_result.stdout.strip().split('\n')[-5:]:
                print(f"   {line}")
            
            if logs_result.stderr:
                print("Error logs:")
                for line in logs_result.stderr.strip().split('\n')[-5:]:
                    print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Error checking container: {e}")


if __name__ == "__main__":
    check_container()
