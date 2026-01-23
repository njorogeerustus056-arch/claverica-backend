# Test override for authentication
def bypass_auth_middleware(get_response):
    def middleware(request):
        # Skip all auth checks
        request.user = type('User', (), {
            'id': 1,
            'email': 'test@claverica.com',
            'is_authenticated': True,
            'is_active': True
        })()
        return get_response(request)
    return middleware
