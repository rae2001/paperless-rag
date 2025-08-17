#!/usr/bin/env python3
"""Simple HTTP server to serve the chat UI."""

import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

def main():
    """Start the chat UI server."""
    # Set up the server
    PORT = 8080
    DIRECTORY = "web-ui"
    
    # Change to the web-ui directory
    if not os.path.exists(DIRECTORY):
        print(f"Error: {DIRECTORY} directory not found!")
        sys.exit(1)
    
    os.chdir(DIRECTORY)
    
    # Create a custom handler that serves chat.html as the default
    class ChatHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def do_GET(self):
            # Serve chat.html for root path
            if self.path == '/':
                self.path = '/chat.html'
            return super().do_GET()
    
    try:
        with socketserver.TCPServer(("", PORT), ChatHandler) as httpd:
            print(f"✓ Chat UI server starting on port {PORT}")
            print(f"✓ Serving from: {os.getcwd()}")
            print(f"✓ Open your browser to: http://localhost:{PORT}")
            print(f"✓ Press Ctrl+C to stop the server")
            print()
            
            # Try to open the browser automatically
            try:
                webbrowser.open(f"http://localhost:{PORT}")
                print("✓ Opening browser automatically...")
            except Exception:
                print("✓ Please open your browser manually")
            
            print()
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"✗ Error: Port {PORT} is already in use")
            print("  Try stopping other servers or use a different port")
        else:
            print(f"✗ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
