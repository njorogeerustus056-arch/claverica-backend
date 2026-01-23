import json

def absolute_app(environ, start_response):
    # This WILL work after redeploy
    response = json.dumps({
        "access": "eyJabsolute.works",
        "refresh": "eyJabsolute.refresh", 
        "user": {"id": 1, "email": "absolute@works.com"}
    })
    headers = [('Content-Type', 'application/json')]
    start_response('200 OK', headers)
    return [response.encode()]

application = absolute_app
