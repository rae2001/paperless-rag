#!/usr/bin/env python3
"""
Start the web UI and ensure API has correct CORS settings.
"""

import subprocess
import sys
import time
import webbrowser
import threading
from pathlib import Path


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


def restart_api():
    """Restart the API with updated CORS settings."""
    print("🔄 Updating API with new CORS settings...")
    
    compose_cmd = detect_docker_compose()
    if not compose_cmd:
        print("❌ Docker Compose not found!")
        return False
    
    need_sudo = not check_docker_permissions()
    sudo_prefix = "sudo " if need_sudo else ""
    
    # Restart the API container
    cmd = f"{sudo_prefix}{compose_cmd} restart rag-api"
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ API restarted successfully")
        return True
    else:
        print("❌ Failed to restart API")
        return False


def start_ui_server():
    """Start the UI server in background."""
    import http.server
    import socketserver
    import os
    
    # Change to web-ui directory
    web_ui_dir = Path("web-ui")
    if not web_ui_dir.exists():
        print("❌ web-ui directory not found!")
        return False
    
    original_dir = os.getcwd()
    os.chdir(web_ui_dir)
    
    PORT = 3001
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers
    class CORSHTTPRequestHandler(Handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            print(f"🌐 UI Server started at: http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ UI Server error: {e}")
    finally:
        os.chdir(original_dir)


def main():
    print("🚀 Starting Paperless RAG Web UI")
    print("=" * 40)
    
    # Check if web-ui exists
    if not Path("web-ui/index.html").exists():
        print("❌ Web UI files not found!")
        sys.exit(1)
    
    # Restart API with updated CORS
    if not restart_api():
        print("⚠️  API restart failed, continuing anyway...")
    
    # Wait for API to start
    print("⏳ Waiting for API to start...")
    time.sleep(5)
    
    # Test API
    try:
        import requests
        response = requests.get("http://192.168.1.77:8088/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
    
    # Start UI server in background thread
    ui_thread = threading.Thread(target=start_ui_server, daemon=True)
    ui_thread.start()
    
    # Wait a moment for server to start
    time.sleep(2)
    
    # Open browser
    url = "http://localhost:3001"
    try:
        webbrowser.open(url)
        print(f"🚀 Opened browser at: {url}")
    except:
        print(f"💡 Please open {url} manually in your browser")
    
    print(f"\n📱 Web UI: {url}")
    print(f"🔗 API: http://192.168.1.77:8088")
    print(f"📄 Paperless: http://192.168.1.77:8000")
    print(f"\n🛑 Press Ctrl+C to stop")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n👋 Shutting down...")


if __name__ == "__main__":
    main()
