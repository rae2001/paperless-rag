#!/usr/bin/env python3
"""
Serve the clean chat UI with proper CORS headers.
This server is designed to work seamlessly with the Paperless RAG API.
"""

import http.server
import socketserver
import os
import sys
import json
from urllib.parse import urlparse

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers."""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory="web-ui", **kwargs)
    
    def end_headers(self):
        """Add CORS headers to every response."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests."""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Serve the clean chat UI by default."""
        if self.path == '/':
            self.path = '/clean-chat.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        """Custom log format."""
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")
        sys.stdout.flush()

def main():
    """Start the web server."""
    PORT = 8080
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           Paperless RAG - Clean Chat UI Server            ║
╚═══════════════════════════════════════════════════════════╝

Starting server...
""")
    
    # Check if web-ui directory exists
    if not os.path.exists("web-ui"):
        print("❌ Error: web-ui directory not found!")
        print("   Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if clean-chat.html exists
    if not os.path.exists("web-ui/clean-chat.html"):
        print("❌ Error: clean-chat.html not found in web-ui directory!")
        sys.exit(1)
    
    try:
        with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
            print(f"✅ Server started successfully!")
            print(f"")
            print(f"📍 Access the chat UI at:")
            print(f"   • http://localhost:{PORT}")
            print(f"   • http://127.0.0.1:{PORT}")
            print(f"   • http://[your-ip]:{PORT}")
            print(f"")
            print(f"🔧 Default API URL: http://localhost:8088")
            print(f"   (Click on the API URL in the UI to change it)")
            print(f"")
            print(f"📝 Logs:")
            print(f"{'─' * 60}")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print(f"\n{'─' * 60}")
                print(f"✅ Server stopped gracefully")
                
    except OSError as e:
        if e.errno == 48 or e.errno == 10048:  # Address already in use (macOS/Linux, Windows)
            print(f"❌ Error: Port {PORT} is already in use!")
            print(f"")
            print(f"Solutions:")
            print(f"1. Stop the other process using port {PORT}")
            print(f"2. Or use a different port by modifying the PORT variable in this script")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
