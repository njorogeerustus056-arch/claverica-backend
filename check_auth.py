import django
import os
import sys

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claverica_backend.settings')
django.setup()

from django.conf import settings
print("Current AUTHENTICATION_BACKENDS:")
for backend in settings.AUTHENTICATION_BACKENDS:
    print(f"  - {backend}")

# Check if EmailBackend exists
try:
    from backend.accounts.backends import EmailBackend
    print("\n✅ EmailBackend module exists")
    
    # Try to instantiate it
    backend = EmailBackend()
    print("✅ EmailBackend can be instantiated")
except Exception as e:
    print(f"\n❌ EmailBackend error: {type(e).__name__}: {e}")
