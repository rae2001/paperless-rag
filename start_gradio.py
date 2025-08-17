#!/usr/bin/env python3
"""
Launch script for the professional Gradio Document Assistant
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_gradio_installed():
    """Check if Gradio is installed"""
    try:
        import gradio
        return True
    except ImportError:
        return False

def install_gradio():
    """Install Gradio requirements"""
    print("Installing Gradio requirements...")
    
    # Try different installation methods
    install_commands = [
        [sys.executable, "-m", "pip", "install", "-r", "gradio_requirements.txt"],
        ["pip3", "install", "-r", "gradio_requirements.txt"],
        ["pip", "install", "-r", "gradio_requirements.txt"],
        [sys.executable, "-m", "pip", "install", "gradio>=4.0.0", "requests>=2.31.0"],
    ]
    
    for i, cmd in enumerate(install_commands, 1):
        print(f"Trying installation method {i}/{len(install_commands)}: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ Gradio installed successfully!")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Method {i} failed: {e}")
            continue
    
    print("❌ All installation methods failed.")
    print("📋 Please install manually:")
    print("   sudo apt install python3-pip")
    print("   pip3 install gradio requests")
    return False

def test_api_connection():
    """Test if API is accessible"""
    try:
        import requests
        response = requests.get("http://192.168.1.77:8088/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print(f"⚠️ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ API test failed: {e}")
        return False

def main():
    print("🚀 Starting Professional Document Assistant")
    print("=" * 50)
    
    # Check if gradio_ui.py exists
    if not Path("gradio_ui.py").exists():
        print("❌ gradio_ui.py not found!")
        sys.exit(1)
    
    # Check/install Gradio
    if not check_gradio_installed():
        print("📦 Gradio not found, installing...")
        if not install_gradio():
            sys.exit(1)
    
    # Test API connection
    print("🔍 Testing API connection...")
    if not test_api_connection():
        print("⚠️ API is not responding. Make sure your Docker containers are running:")
        print("   docker-compose up -d")
        print("")
        print("🔄 Continuing anyway - API status will be shown in the interface...")
    
    # Start Gradio
    print("🌐 Starting Document Assistant...")
    print("📍 Interface will be available at: http://192.168.1.77:7860")
    print("🏢 Professional interface ready for company staff")
    print("🔧 API: http://192.168.1.77:8088")
    print("📄 Paperless: http://192.168.1.77:8000")
    print("")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and run the Gradio interface
        from gradio_ui import main as run_gradio
        run_gradio()
    except KeyboardInterrupt:
        print("\n👋 Document Assistant stopped")
    except Exception as e:
        print(f"❌ Failed to start interface: {e}")
        print("💡 Try installing Gradio manually: pip install gradio requests")
        sys.exit(1)

if __name__ == "__main__":
    main()
