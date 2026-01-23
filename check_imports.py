import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('.')
django.setup()

print("=== Checking all imports in views_fixed.py ===")

# Manually test each import
imports_to_check = [
    'rest_framework.views.APIView',
    'rest_framework.response.Response', 
    'rest_framework.permissions.AllowAny',
    'rest_framework_simplejwt.tokens.RefreshToken',
    'django.contrib.auth.get_user_model',
]

for imp in imports_to_check:
    try:
        # Try to import
        exec(f'import {imp.split(".")[0]}')
        print(f"✅ {imp}")
    except ImportError as e:
        print(f"❌ {imp}: {e}")

# Check the actual view execution with more detail
print("\n=== Detailed view test ===")
from backend.accounts.views_fixed import FixedAuthView
from rest_framework.test import APIRequestFactory
import json

view = FixedAuthView()
factory = APIRequestFactory()

# Test 1: Empty request
request1 = factory.post('/api/auth/login/', 
                       data=json.dumps({}),
                       content_type='application/json')
try:
    response1 = view.post(request1)
    print(f"✅ Empty request: {response1.status_code}")
    print(f"   Data: {response1.data}")
except Exception as e:
    print(f"❌ Empty request failed: {type(e).__name__}: {e}")

# Test 2: With data
request2 = factory.post('/api/auth/login/',
                       data=json.dumps({"email": "test", "password": "test"}),
                       content_type='application/json')
try:
    response2 = view.post(request2)
    print(f"✅ With data: {response2.status_code}")
    print(f"   Has access token: {'access' in response2.data}")
except Exception as e:
    print(f"❌ With data failed: {type(e).__name__}: {e}")
