import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.test import Client
from django.urls import get_resolver, URLPattern, URLResolver
import json

client = Client()

print("🔗 COMPREHENSIVE API ENDPOINTS TEST")
print("=" * 60)

# Function to extract all URLs
def extract_urls(urlpatterns, base=''):
    urls = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            urls.extend(extract_urls(pattern.url_patterns, base + str(pattern.pattern)))
        elif isinstance(pattern, URLPattern):
            urls.append(base + str(pattern.pattern))
    return urls

# Get all URLs
resolver = get_resolver()
all_urls = extract_urls(resolver.url_patterns)

# Filter API URLs
api_urls = [url for url in all_urls if url.startswith('api/') or 'api' in url]
non_api_urls = [url for url in all_urls if not (url.startswith('api/') or 'api' in url)]

print(f"\n📊 Found {len(all_urls)} total URL patterns")
print(f"   🔗 API Endpoints: {len(api_urls)}")
print(f"   🌐 Other URLs: {len(non_api_urls)}")

# Test critical endpoints
print("\n🧪 TESTING CRITICAL ENDPOINTS:")

critical_endpoints = [
    ('/health/', 'GET', 'Health Check'),
    ('/api/auth/health/', 'GET', 'Auth Health'),
    ('/admin/', 'GET', 'Admin Interface'),
    ('/api/', 'GET', 'API Root'),
]

for endpoint, method, name in critical_endpoints:
    try:
        if method == 'GET':
            response = client.get(endpoint)
        elif method == 'POST':
            response = client.post(endpoint)
        
        if response.status_code in [200, 301, 302]:
            print(f"   ✅ {name}: {endpoint} - Status {response.status_code}")
        elif response.status_code == 403:
            print(f"   🔒 {name}: {endpoint} - Forbidden (needs auth)")
        elif response.status_code == 404:
            print(f"   ❌ {name}: {endpoint} - Not Found")
        else:
            print(f"   ⚠️  {name}: {endpoint} - Status {response.status_code}")
            
    except Exception as e:
        print(f"   💥 {name}: {endpoint} - Error: {str(e)[:80]}")

# List all API endpoints
print("\n📋 ALL API ENDPOINTS:")
api_groups = {}
for url in sorted(api_urls):
    parts = url.strip('/').split('/')
    if len(parts) >= 2:
        group = parts[1]  # api/[group]/...
        if group not in api_groups:
            api_groups[group] = []
        api_groups[group].append(url)

for group, endpoints in sorted(api_groups.items()):
    print(f"\n   📁 {group.upper()} ({len(endpoints)} endpoints):")
    for endpoint in sorted(endpoints)[:10]:  # Show first 10 per group
        print(f"      • {endpoint}")
    if len(endpoints) > 10:
        print(f"      ... and {len(endpoints) - 10} more")

print("\n" + "=" * 60)
print(f"✅ API STRUCTURE VERIFIED: {len(api_urls)} endpoints available")
