#!/usr/bin/env python3
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

print("🔥 DIRECT SERVER")

class DirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()
    
    def do_POST(self):
        self.handle_request()
    
    def do_PUT(self):
        self.handle_request()
    
    def do_DELETE(self):
        self.handle_request()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def handle_request(self):
        response = {
            "server": "direct",
            "access": "eyJdirect.token",
            "refresh": "eyJdirect.refresh",
            "user": {
                "id": 1,
                "email": "direct@server.com",
                "path": self.path
            }
        }
        
        body = json.dumps(response).encode()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 18000))  # Use different port
    print(f"🚀 Starting on port {port}")
    server = HTTPServer(('0.0.0.0', port), DirectHandler)
    server.serve_forever()
