#!/usr/bin/env python3
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {
            "status": "DEPLOY_NOW_ACTIVE",
            "access": "eyJdeploy.now",
            "refresh": "eyJdeploy.refresh",
            "user": {"id": 1, "email": "deploy@now.com"}
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.do_GET()  # Same response for POST
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Silence logs

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Use 8080 for testing
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"🚀 DEPLOY_NOW server starting on port {port}")
    print(f"✅ Will respond to ALL requests with tokens")
    server.serve_forever()
