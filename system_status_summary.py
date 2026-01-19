import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection

print("🔍 CLAVERICA PLATFORM - COMPREHENSIVE STATUS")
print("=" * 60)

# 1. Django & Database
print("\n1️⃣  CORE INFRASTRUCTURE:")
print(f"   ✅ Django {django.get_version()}")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version()")
        db_version = cursor.fetchone()[0]
    print(f"   ✅ Database: {db_version[:50]}...")
except:
    print("   ❌ Database connection failed")

# 2. Apps & Models
print("\n2️⃣  APPS & MODELS:")
User = get_user_model()
print(f"   ✅ Custom User Model: {User._meta.label}")

# Count all backend apps
backend_apps = [app for app in apps.get_app_configs() if 'backend' in app.name]
print(f"   📦 Backend Apps: {len(backend_apps)}")

# Count all models
total_models = sum(len(list(app.get_models())) for app in backend_apps)
print(f"   🗄️  Total Models: {total_models}")

# 3. Admin Interface
print(f"\n3️⃣  ADMIN INTERFACE:")
print(f"   👑 Registered Models: {len(admin.site._registry)}")
print(f"   🔐 Superusers: {User.objects.filter(is_superuser=True).count()}")

# 4. URLs
from django.urls import get_resolver
url_count = 0
def count_urls(urlpatterns):
    count = 0
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            count += count_urls(pattern.url_patterns)
        else:
            count += 1
    return count

url_count = count_urls(get_resolver().url_patterns)
print(f"\n4️⃣  API ENDPOINTS:")
print(f"   🔗 Total URL Patterns: {url_count}")

# 5. Settings Check
from django.conf import settings
print(f"\n5️⃣  SETTINGS CHECK:")
print(f"   🛡️  DEBUG: {settings.DEBUG}")
print(f"   🌐 ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"   📧 EMAIL BACKEND: {settings.EMAIL_BACKEND}")
print(f"   🗄️  DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")

# 6. List all backend apps
print(f"\n6️⃣  BACKEND MICROSERVICES:")
for app in sorted(backend_apps, key=lambda x: x.name):
    models = list(app.get_models())
    print(f"   • {app.name}: {len(models)} models")
    for model in models:
        print(f"      - {model.__name__}")

print("\n" + "=" * 60)
print("🎯 READY FOR FUNCTIONAL TESTING!")
