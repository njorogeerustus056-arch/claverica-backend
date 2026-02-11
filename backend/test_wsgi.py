"""
Minimal WSGI app for Railway testing
"""
def application(environ, start_response):
    """Always returns 200 OK - no Django, no database, no nothing"""
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'OK - Railway Health Check Passed!']
