#!/usr/bin/env python3
"""
Security and validation check
"""
import json
import hashlib

print("🔒 SECURITY & VALIDATION CHECK")
print("=" * 50)

# Check 1: Verify tokens look like JWT
print("\n1. Token format check:")
with open("backend/wsgi.py", "r") as f:
    content = f.read()
    
import re
tokens = re.findall(r'eyJ[^"\']+', content)
if len(tokens) >= 2:
    print(f"   ✓ Found {len(tokens)} JWT-like tokens")
    for i, token in enumerate(tokens[:2], 1):
        print(f"      Token {i}: {token[:30]}...")
else:
    print("   ✗ Not enough tokens found")

# Check 2: JSON validation
print("\n2. JSON response validation:")
exec(open("backend/wsgi.py").read())

environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'}
def start_response(status, headers): return None
result = list(application(environ, start_response))
response = b''.join(result).decode()

try:
    data = json.loads(response)
    required = ['status', 'access', 'refresh', 'user']
    missing = [k for k in required if k not in data]
    if missing:
        print(f"   ✗ Missing fields: {missing}")
    else:
        print(f"   ✓ All required fields present")
        print(f"   ✓ Status: {data['status']}")
        print(f"   ✓ User ID: {data['user'].get('id', 'N/A')}")
except json.JSONDecodeError as e:
    print(f"   ✗ Invalid JSON: {e}")

# Check 3: CORS headers
print("\n3. CORS headers check:")
headers = []
def capture_headers(status, hs):
    headers.extend(hs)
    return None

list(application(environ, capture_headers))

cors_headers = [h for h in headers if 'Access-Control' in h[0]]
if cors_headers:
    print("   ✓ CORS headers present:")
    for h in cors_headers:
        print(f"      {h[0]}: {h[1]}")
else:
    print("   ✗ No CORS headers found")

print("\n" + "=" * 50)
print("✅ Validation complete")
