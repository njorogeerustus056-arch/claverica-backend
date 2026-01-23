"""
Simple ASGI application
"""
import json

async def app(scope, receive, send):
    if scope['type'] != 'http':
        return
    
    # Get method and path
    method = scope['method']
    path = scope['path']
    
    print(f"[ASGI] {method} {path}")
    
    # For POST requests, return auth tokens
    if method == 'POST':
        # Read request body
        body = b''
        more_body = True
        while more_body:
            message = await receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)
        
        try:
            if body:
                data = json.loads(body.decode('utf-8'))
            else:
                data = {}
        except:
            data = {}
        
        email = data.get('email', data.get('username', 'admin@claverica.com'))
        
        response_data = {
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhc2dpIjoic2ltcGxlIiwidXNlcl9pZCI6MSwiZW1haWwiOiJhZG1pbkBjbGF2ZXJpY2EuY29tIiwiZXhwIjoxOTk5OTk5OTk5fQ.asgi_simple_signature",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhc2dpIjoic2ltcGxlX3JlZnJlc2giLCJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGNsYXZlcmljYS5jb20iLCJleHAiOjE5OTk5OTk5OTl9.asgi_simple_refresh",
            "user": {
                "id": 1,
                "email": email,
                "name": "ASGI Simple Admin"
            }
        }
        
        response_json = json.dumps(response_data)
        
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'application/json'],
                [b'x-auth-system', b'ASGI-Simple-Override']
            ]
        })
        
        await send({
            'type': 'http.response.body',
            'body': response_json.encode('utf-8')
        })
        return
    
    # For GET requests
    response_data = {
        "status": "ok",
        "service": "Simple Auth ASGI",
        "message": "POST to any endpoint for auth tokens"
    }
    
    response_json = json.dumps(response_data)
    
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'application/json']
        ]
    })
    
    await send({
        'type': 'http.response.body',
        'body': response_json.encode('utf-8')
    })
