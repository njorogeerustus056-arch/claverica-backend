import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
try:
    import django
    django.setup()
    
    from django.conf import settings
    print("REST_FRAMEWORK settings:")
    for key, value in settings.REST_FRAMEWORK.items():
        print(f"  {key}: {value}")
        
    print("\nMiddleware (first 5):")
    for mw in settings.MIDDLEWARE[:5]:
        print(f"  {mw}")
        
except Exception as e:
    print(f"Error: {e}")
