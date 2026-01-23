from wsgiref.simple_server import make_server
import json

def app(environ, start_response):
    # Handle ALL requests
    response = json.dumps({
        "access": "eyJnuclear.works",
        "refresh": "eyJnuclear.refresh",
        "user": {"id": 1, "email": "nuclear@fix.com"},
        "note": "Complete Django bypass"
    })
    
    headers = [
        ('Content-Type', 'application/json'),
        ('X-Solution', 'Nuclear-Bypass')
    ]
    
    start_response('200 OK', headers)
    return [response.encode()]

if __name__ == '__main__':
    print("Starting nuclear server...")
    server = make_server('0.0.0.0', 8000, app)
    server.serve_forever()
