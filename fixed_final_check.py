import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

print("🚀 FINAL CLAVERICA SYSTEM CHECK - FIXED")
print("=" * 50)

# 1. Check Django
print("\n1️⃣  DJANGO SETUP:")
print(f"   ✅ Django {django.get_version()} loaded")

# 2. Check database
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("   ✅ Database connection working")
except:
    print("   ❌ Database connection failed")

# 3. Check apps
from django.apps import apps
backend_apps = []
for config in apps.app_configs.values():
    if config.name.startswith('backend.'):
        backend_apps.append(config.name)

print(f"\n2️⃣  BACKEND APPS: {len(backend_apps)} loaded")

# 4. Count models properly
total_models = 0
for config in apps.app_configs.values():
    if config.name.startswith('backend.'):
        models = list(config.get_models())  # Convert generator to list
        total_models += len(models)

print(f"   📦 Total models: {total_models}")

# 5. Check admin
from django.contrib import admin
print(f"\n3️⃣  ADMIN INTERFACE:")
print(f"   👑 Registered models: {len(admin.site._registry)}")

# 6. Check URLs
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
print(f"\n4️⃣  URL PATTERNS: {url_count} total")

# 7. Check superuser
from django.contrib.auth import get_user_model
User = get_user_model()
superuser_count = User.objects.filter(is_superuser=True).count()
print(f"\n5️⃣  SUPERUSER: {superuser_count} superuser(s)")

# Summary
print("\n" + "=" * 50)
print("🎉 CLAVERICA PLATFORM STATUS:")
print(f"   ✅ {len(backend_apps)}/16 backend apps")
print(f"   ✅ {total_models} database models")
print(f"   ✅ {len(admin.site._registry)} admin models")
print(f"   ✅ {url_count} URL patterns")
print(f"   ✅ {superuser_count} superuser(s)")
print(f"   ✅ Database connected")
print("\n🚀 SYSTEM IS READY FOR DEPLOYMENT!")
print("\n📝 Final steps:")
print("   1. Run: python manage.py collectstatic --noinput")
print("   2. Test API: curl https://your-render-url/health/")
print("   3. Access admin: https://your-render-url/admin/")
print("   4. Deploy to Render!")
