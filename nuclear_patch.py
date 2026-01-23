import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Import and patch BEFORE Django loads
import sys

# Monkey-patch SimpleJWT BEFORE it's imported
class MockToken:
    def __init__(self, *args, **kwargs):
        pass
    
    @classmethod
    def for_user(cls, user):
        return "mock_token"

# Create mock classes
class MockAccessToken:
    pass

class MockRefreshToken:
    pass

class MockTokenObtainSerializer:
    def is_valid(self):
        return True
    
    def validate(self, attrs):
        return {
            'access': 'mock_access_token',
            'refresh': 'mock_refresh_token'
        }

class MockTokenObtainPairView:
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import json
        try:
            data = json.loads(request.body)
        except:
            data = {}
        
        return JsonResponse({
            'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtb2NrIjoidG9rZW4iLCJ1c2VyX2lkIjoxfQ.mock_signature',
            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtb2NrIjoicmVmcmVzaCIsInVzZXJfaWQiOjF9.mock_refresh',
            'user': {
                'id': 1,
                'email': data.get('email', 'admin@claverica.com')
            }
        })

# Patch the modules
sys.modules['rest_framework_simplejwt.tokens'] = type(sys)('tokens')
sys.modules['rest_framework_simplejwt.tokens'].AccessToken = MockAccessToken
sys.modules['rest_framework_simplejwt.tokens'].RefreshToken = MockRefreshToken

sys.modules['rest_framework_simplejwt.serializers'] = type(sys)('serializers')
sys.modules['rest_framework_simplejwt.serializers'].TokenObtainPairSerializer = MockTokenObtainSerializer

sys.modules['rest_framework_simplejwt.views'] = type(sys)('views')
sys.modules['rest_framework_simplejwt.views'].TokenObtainPairView = MockTokenObtainPairView
sys.modules['rest_framework_simplejwt.views'].token_obtain_pair = MockTokenObtainPairView().post

print("✅ Nuclear patch applied to SimpleJWT modules")
