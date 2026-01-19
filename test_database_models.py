import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.apps import apps
from django.db import connection, DatabaseError

print("🗄️ DATABASE MODELS TEST")
print("=" * 50)

# Get all backend apps
backend_apps = [app for app in apps.get_app_configs() if 'backend' in app.name]

print(f"\n📊 Testing {len(backend_apps)} backend apps:")

all_models_ok = True
for app in sorted(backend_apps, key=lambda x: x.name):
    models = list(app.get_models())
    print(f"\n🔍 {app.name}:")
    
    for model in models:
        model_name = model.__name__
        try:
            # Try to query the model
            count = model.objects.count()
            print(f"   ✅ {model_name}: {count} records")
            
            # Try to get fields
            fields = [f.name for f in model._meta.get_fields() if hasattr(f, 'name')]
            print(f"      Fields: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
            
        except DatabaseError as e:
            print(f"   ❌ {model_name}: Database error - {str(e)[:80]}")
            all_models_ok = False
        except Exception as e:
            print(f"   ⚠️  {model_name}: {str(e)[:80]}")
            all_models_ok = False

# Test database operations
print("\n🧪 DATABASE OPERATIONS TEST:")
try:
    with connection.cursor() as cursor:
        # Test raw SQL
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        print(f"   ✅ Database has {table_count} tables")
        
        # Test transaction
        cursor.execute("BEGIN")
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        cursor.execute("ROLLBACK")
        print(f"   ✅ Transactions working: {result[0]}")
        
except Exception as e:
    print(f"   ❌ Database operations failed: {str(e)[:100]}")
    all_models_ok = False

print("\n" + "=" * 50)
if all_models_ok:
    print("✅ ALL DATABASE MODELS ARE WORKING!")
else:
    print("⚠️  Some database models need attention")
