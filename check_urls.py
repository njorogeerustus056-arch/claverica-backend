import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
try:
    import django
    django.setup()
    
    from django.urls import get_resolver
    resolver = get_resolver()
    
    print("Testing URL patterns:")
    for pattern in resolver.url_patterns[:5]:
        print(f"  Pattern: {pattern.pattern}")
        
except Exception as e:
    print(f"Error: {e}")
