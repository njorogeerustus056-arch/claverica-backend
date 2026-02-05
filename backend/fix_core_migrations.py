import sqlite3
import datetime
from django.conf import settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django
django.setup()

db_path = settings.DATABASES['default']['NAME']
print(f"Database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n=== RESETTING MIGRATIONS FOR CORE APPS ONLY ===")

# List ONLY the core apps we care about
CORE_APPS = [
    'users',
    'accounts', 
    'cards',
    'transactions',
    'payments',
    'transfers'
]

# 1. Clear ALL migration records
cursor.execute("DELETE FROM django_migrations")
print("✓ Cleared all migration history")

# 2. Add auth.0012 FIRST (to satisfy the dependency)
now = datetime.datetime.now().isoformat()
cursor.execute(
    "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
    ('auth', '0012_alter_user_first_name_max_length', now)
)
print("✓ Added auth.0012 (dependency for accounts)")

# 3. Add contenttypes (another dependency)
cursor.execute(
    "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
    ('contenttypes', '0001_initial', now)
)
cursor.execute(
    "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
    ('contenttypes', '0002_remove_content_type_name', now)
)

# 4. Now add ALL our core app migrations
for app in CORE_APPS:
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
        (app, '0001_initial', now)
    )
    print(f"✓ Added {app}.0001_initial")

conn.commit()
conn.close()

print("\n✅ MIGRATION FIX COMPLETE!")
print("Now run: python manage.py migrate --fake")
print("\nCore apps are ready:")
for app in CORE_APPS:
    print(f"  - {app}")
