#!/bin/bash
echo "=== COMPREHENSIVE LOCAL TEST ==="
echo ""

# 1. Test direct HTTP server
echo "1. Testing direct HTTP server..."
python3 -c "
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import urllib.request

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'test': 'direct_http_works'}
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.do_GET()

def run_server():
    server = HTTPServer(('localhost', 9999), TestHandler)
    server.serve_forever()

# Start server in background
import threading
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# Give it time to start
import time
time.sleep(1)

# Test it
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:9999/test')
    print(f'✓ Direct HTTP: {response.read().decode()}')
except Exception as e:
    print(f'✗ Direct HTTP failed: {e}')
" 2>/dev/null

echo ""

# 2. Test WSGI
echo "2. Testing WSGI..."
python3 -c "
import sys
import json

# Create a test WSGI app
def test_app(environ, start_response):
    response = {'wsgi': 'test_passed'}
    body = json.dumps(response).encode()
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(body)))
    ]
    start_response('200 OK', headers)
    return [body]

# Test it
def start_response(status, headers):
    print(f'  Status: {status}')
    return None

environ = {
    'REQUEST_METHOD': 'GET',
    'PATH_INFO': '/test'
}

result = list(test_app(environ, start_response))
print(f'✓ WSGI test passed: {b\"\".join(result).decode()}')
" 2>/dev/null

echo ""

# 3. Test your actual wsgi.py
echo "3. Testing your backend/wsgi.py..."
if [ -f "backend/wsgi.py" ]; then
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    exec(open('backend/wsgi.py').read())
    
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/api/auth/login/',
        'CONTENT_TYPE': 'application/json'
    }
    
    def start_response(status, headers):
        print(f'  Status: {status}')
        for h in headers:
            if h[0] == 'Content-Type':
                print(f'  Content-Type: {h[1]}')
        return None
    
    result = list(application(environ, start_response))
    print('✓ Your wsgi.py works!')
    print(f'  Response length: {len(b\"\".join(result))} bytes')
except Exception as e:
    print(f'✗ Your wsgi.py failed: {e}')
" 2>/dev/null
else
    echo "✗ backend/wsgi.py not found"
fi

echo ""
echo "=== TEST COMPLETE ==="
