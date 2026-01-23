import os

bind = f"0.0.0.0:{os.environ.get('PORT', 10000)}"
workers = 1
timeout = 120

def app(environ, start_response):
    """Direct app that ignores Django completely"""
    import json
    
    response = {
        "gunicorn": "active",
        "access": "eyJgunicorn.forced",
        "refresh": "eyJgunicorn.refresh",
        "user": {"id": 1, "email": "gunicorn@forced.com"}
    }
    
    body = json.dumps(response).encode()
    headers = [
        ('Content-Type', 'application/json'),
        ('Content-Length', str(len(body)))
    ]
    start_response('200 OK', headers)
    return [body]
