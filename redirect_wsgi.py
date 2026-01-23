import json

def redirect_app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    # For auth requests, return fixed response
    if method == 'POST' and ('auth' in path or 'login' in path or 'token' in path):
        response = json.dumps({
            "access": "eyJredirect.fixed",
            "refresh": "eyJredirect.refresh",
            "user": {"id": 1, "email": "redirect@fixed.com"}
        })
        headers = [('Content-Type', 'application/json')]
        start_response('200 OK', headers)
        return [response.encode()]
    
    # For other requests, show message
    response = json.dumps({
        "message": "Use POST to /auth/, /login/, or /token/ endpoints",
        "status": "redirect_active"
    })
    headers = [('Content-Type', 'application/json')]
    start_response('200 OK', headers)
    return [response.encode()]

application = redirect_app
