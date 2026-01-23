#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

print("Testing import order...")

# First, try to import Django to see if it loads
try:
    import django
    print("⚠️  Django IS importable from sys.path")
    
    # Check if it's our patched version
    if hasattr(django, '__file__'):
        print(f"   Django location: {django.__file__}")
except ImportError:
    print("✓ Django is NOT importable (good!)")

print("\nTesting wsgi import...")
try:
    # Direct import of our wsgi
    import backend.wsgi
    print(f"✓ backend.wsgi imports successfully")
    print(f"   Application type: {type(backend.wsgi.application)}")
    
    # Test it
    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'}
    def start_response(status, headers):
        print(f"   WSGI returns: {status}")
        return None
    
    result = list(backend.wsgi.application(environ, start_response))
    print(f"   Response length: {len(b''.join(result))} bytes")
    
except Exception as e:
    print(f"✗ backend.wsgi import failed: {e}")

print("\n✅ Verification complete")
