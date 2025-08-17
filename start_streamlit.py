#!/usr/bin/env python3
"""
Start the Streamlit UI for Paperless RAG Q&A System
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def check_streamlit_installed():
    """Check if Streamlit is installed"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_streamlit():
    """Install Streamlit requirements"""
    print("📦 Installing Streamlit requirements...")
    
    # Try different installation methods
    install_commands = [
        # Method 1: pip module
        [sys.executable, "-m", "pip", "install", "-r", "streamlit_requirements.txt"],
        # Method 2: pip3 directly
        ["pip3", "install", "-r", "streamlit_requirements.txt"],
        # Method 3: pip directly
        ["pip", "install", "-r", "streamlit_requirements.txt"],
    ]
    
    for i, cmd in enumerate(install_commands, 1):
        print(f"   Trying method {i}/{len(install_commands)}: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ Streamlit installed successfully!")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"   ❌ Method {i} failed: {e}")
            continue
    
    print(f"❌ All installation methods failed.")
    print(f"📋 Please install manually using one of these commands:")
    print(f"   sudo apt install python3-streamlit python3-requests  # Ubuntu/Debian")
    print(f"   sudo apt install python3-pip && pip3 install streamlit requests")
    print(f"   conda install streamlit requests  # If you have conda")
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
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
        return False

def main():
    print("🚀 Starting Paperless RAG Streamlit UI")
    print("=" * 45)
    
    # Check if streamlit_ui.py exists
    if not Path("streamlit_ui.py").exists():
        print("❌ streamlit_ui.py not found!")
        sys.exit(1)
    
    # Check/install Streamlit
    if not check_streamlit_installed():
        print("📦 Streamlit not found, installing...")
        if not install_streamlit():
            print("❌ Failed to install Streamlit. Please install manually:")
            print("   pip install streamlit requests")
            sys.exit(1)
    
    # Test API connection
    print("🔍 Testing API connection...")
    if not test_api_connection():
        print("⚠️  API is not responding. Make sure your Docker containers are running:")
        print("   docker-compose up -d")
        print("")
        print("🔄 Continuing anyway - you can check API status in the Streamlit sidebar...")
    
    # Start Streamlit
    print("🌐 Starting Streamlit UI...")
    print("📱 The UI will open in your browser automatically")
    print("🔗 API: http://192.168.1.77:8088")
    print("📄 Paperless: http://192.168.1.77:8000")
    print("")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 45)
    
    try:
        # Run Streamlit with custom config
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_ui.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Streamlit UI stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
