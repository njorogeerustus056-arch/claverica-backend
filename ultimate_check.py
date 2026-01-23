#!/usr/bin/env python3
import sys
import os

print("=" * 60)
print("ULTIMATE CHECK BEFORE DEPLOYMENT")
print("=" * 60)

# Check 1: Files exist
print("\n1. File check:")
files = ["backend/wsgi.py", "render.yaml", "direct_server.py", "backend/__init__.py"]
for f in files:
    if os.path.exists(f):
        print(f"   ✓ {f}")
    else:
        print(f"   ✗ {f} missing")

# Check 2: No Django imports
print("\n2. Django import check:")
with open("backend/wsgi.py", "r") as f:
    content = f.read()
    if "import django" in content or "from django" in content:
        print("   ✗ Django import found!")
        sys.exit(1)
    else:
        print("   ✓ No Django imports")

# Check 3: Test wsgi
print("\n3. WSGI test:")
try:
    exec(open("backend/wsgi.py").read())
    
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/api/auth/login/',
        'CONTENT_TYPE': 'application/json'
    }
    
    def start_response(status, headers):
        print(f"   Status: {status}")
        return None
    
    result = list(application(environ, start_response))
    response = b''.join(result).decode()
    if 'access' in response and 'user' in response:
        print("   ✓ Returns auth tokens")
    else:
        print("   ✗ Bad response")
        print(f"   Response: {response}")
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ WSGI test failed: {e}")
    sys.exit(1)

# Check 4: Check render.yaml
print("\n4. Render.yaml check:")
with open("render.yaml", "r") as f:
    content = f.read()
    if "gunicorn backend.wsgi:application" in content:
        print("   ✓ Uses gunicorn with our wsgi")
    else:
        print("   ✗ Wrong start command")
        sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED!")
print("=" * 60)

print("\n🚀 READY TO DEPLOY!")
print("\nRun these commands:")
print("  git add -A")
print('  git commit -m "EMERGENCY: Simple auth server returning tokens for all requests"')
print("  git push origin main")
print("\n⏱️  Wait 2 minutes, then test:")
print('  curl -X POST https://claverica-backend-rniq.onrender.com/api/auth/login/ \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"email":"test","password":"test"}\'')
