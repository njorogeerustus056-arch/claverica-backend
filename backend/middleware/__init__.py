# ForceAuthMiddleware stub - created to fix import errors
# This is a temporary stub to allow Django to start

class ForceAuthMiddleware:
    """Stub middleware to fix import errors"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Do nothing
        return None
