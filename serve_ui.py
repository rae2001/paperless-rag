#!/usr/bin/env python3
"""
Simple web server to serve the RAG UI.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path


def main():
    # Change to web-ui directory
    web_ui_dir = Path("web-ui")
    if not web_ui_dir.exists():
        print("❌ web-ui directory not found!")
        sys.exit(1)
    
    os.chdir(web_ui_dir)
    
    # Start simple HTTP server
    PORT = 3001
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers for local development
    class CORSHTTPRequestHandler(Handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"🌐 Serving Paperless RAG UI at: {url}")
            print(f"📱 Open this URL in your browser: {url}")
            print(f"🔗 API running at: http://localhost:8088")
            print(f"📄 Paperless at: http://192.168.1.77:8000")
            print(f"\n🛑 Press Ctrl+C to stop the server")
            
            # Try to open browser automatically
            try:
                webbrowser.open(url)
                print(f"🚀 Opened browser automatically")
            except:
                print(f"💡 Please open {url} manually in your browser")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    main()
