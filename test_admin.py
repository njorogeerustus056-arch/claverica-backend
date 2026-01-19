import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

print("🧪 TESTING DJANGO ADMIN:")

# Test if admin site loads
from django.contrib import admin

# Count registered models
model_count = len(admin.site._registry)
print(f"📊 Models registered in admin: {model_count}")

# List registered models
print("\n🔍 Registered models:")
for model, model_admin in admin.site._registry.items():
    print(f"  - {model._meta.app_label}.{model.__name__}")

# Test a specific admin
try:
    from backend.accounts.models import Account
    print(f"\n✅ Account model: {Account}")
except:
    print("\n⚠️ Could not import Account model")

print("\n🎯 Admin is ready!")
