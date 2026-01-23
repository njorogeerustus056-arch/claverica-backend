import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.urls import get_resolver
import re

print("🔍 ACTUAL API ENDPOINTS AVAILABLE:")
print("=" * 60)

all_urls = []

def get_urls(patterns, prefix=''):
    for pattern in patterns:
        if hasattr(pattern, 'pattern'):
            url = prefix + str(pattern.pattern)
            if hasattr(pattern, 'callback'):
                name = pattern.name
                callback = pattern.callback
                if 'api' in url:
                    all_urls.append((url, name))
            elif hasattr(pattern, 'url_patterns'):
                get_urls(pattern.url_patterns, url.rstrip('/') + '/')

resolver = get_resolver()
get_urls(resolver.url_patterns)

# Sort and print API endpoints
api_endpoints = sorted([url for url, name in all_urls if 'api' in url])
for endpoint in api_endpoints:
    print(f"✓ {endpoint}")

print(f"\n📊 Total API endpoints found: {len(api_endpoints)}")
print(f"❌ Missing critical endpoints from frontend:")
missing = [
    '/api/users/profile/',
    '/api/notifications/notifications/',
    '/api/transactions/',
    '/api/kyc/verifications/my_status/',
    '/api/compliance/limits/',
]
for m in missing:
    if m.rstrip('/') not in [e.rstrip('/') for e in api_endpoints]:
        print(f"   - {m}")
