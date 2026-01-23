import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.db import connection

print("=== DATABASE TABLES vs MODELS ===")

# Get all tables
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        AND table_name NOT LIKE 'django_%'
        AND table_name NOT LIKE 'auth_%'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]

print(f"📊 Database has {len(tables)} tables")

# Check which have models
from django.apps import apps
all_models = []
for config in apps.app_configs.values():
    all_models.extend(config.get_models())

model_tables = [model._meta.db_table for model in all_models]

print(f"📊 Django knows {len(model_tables)} tables")

# Missing tables (in DB but no model)
missing = [t for t in tables if t not in model_tables]
if missing:
    print(f"\n🚨 {len(missing)} TABLES WITHOUT MODELS:")
    for table in missing[:10]:
        print(f"  - {table}")
    if len(missing) > 10:
        print(f"  ... and {len(missing)-10} more")
else:
    print("\n✅ All database tables have models!")
