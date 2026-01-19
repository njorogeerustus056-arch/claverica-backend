import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

print("🔗 TESTING API ENDPOINTS:")

# Import DRF if available
try:
    from rest_framework.test import APIClient
    client = APIClient()
    print("✅ Django REST Framework loaded")
    
    # Test health endpoint
    try:
        from django.urls import reverse
        health_url = reverse('health-check')
        print(f"✅ Health endpoint: {health_url}")
    except:
        print("⚠️ Health endpoint not configured")
    
    # List available API endpoints
    from django.urls import get_resolver
    
    print("\n📋 Available API patterns:")
    api_patterns = []
    
    def extract_urls(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            elif hasattr(pattern, 'pattern'):
                full_pattern = prefix + str(pattern.pattern)
                if 'api' in full_pattern or 'api' in str(pattern):
                    api_patterns.append(full_pattern)
    
    extract_urls(get_resolver().url_patterns)
    
    # Show first 10 API endpoints
    for url in sorted(set(api_patterns))[:10]:
        print(f"  • {url}")
    
    print(f"\n📊 Total API endpoints found: {len(set(api_patterns))}")
    
except ImportError:
    print("⚠️ Django REST Framework not available")

print("\n🎯 API testing complete!")
