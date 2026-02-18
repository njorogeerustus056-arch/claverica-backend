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

print("\n=== ADDING COMPLETE AUTH MIGRATION CHAIN ===")

# List ALL auth migrations in correct order
AUTH_MIGRATIONS = [
    '0001_initial',
    '0002_alter_permission_name_max_length',
    '0003_alter_user_email_max_length',
    '0004_alter_user_username_opts',
    '0005_alter_user_last_login_null',
    '0006_require_contenttypes_0002',
    '0007_alter_validators_add_error_messages',
    '0008_alter_user_username_max_length',
    '0009_alter_user_last_name_max_length',
    '0010_alter_group_name_max_length',
    '0011_update_proxy_permissions',
    '0012_alter_user_first_name_max_length'
]

# Core apps we care about
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
print(" Cleared all migration history")

# 2. Add contenttypes FIRST (auth depends on this)
now = datetime.datetime.now().isoformat()
cursor.execute(
    "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
    ('contenttypes', '0001_initial', now)
)
cursor.execute(
    "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
    ('contenttypes', '0002_remove_content_type_name', now)
)
print(" Added contenttypes migrations")

# 3. Add ALL auth migrations in sequence
for migration in AUTH_MIGRATIONS:
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
        ('auth', migration, now)
    )
print(f" Added {len(AUTH_MIGRATIONS)} auth migrations")

# 4. Add our core app migrations
for app in CORE_APPS:
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)",
        (app, '0001_initial', now)
    )
print(f" Added {len(CORE_APPS)} core app migrations")

conn.commit()
conn.close()

print(f"\n Added TOTAL: {2 + len(AUTH_MIGRATIONS) + len(CORE_APPS)} migration records")
print("\nNOW RUN: python manage.py migrate --fake")
