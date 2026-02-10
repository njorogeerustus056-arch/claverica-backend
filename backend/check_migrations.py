import sqlite3
import os
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django
django.setup()

db_path = settings.DATABASES['default']['NAME']
print(f'Database: {db_path}')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check migration table
cursor.execute('SELECT id, app, name, applied FROM django_migrations ORDER BY id')
rows = cursor.fetchall()

print('\n=== CURRENT MIGRATION STATE ===')
print(f'Total migrations: {len(rows)}')
for row in rows:
    print(f'{row[0]:3} | {row[1]:15} | {row[2]:25} | {row[3]}')

# Check specifically for accounts vs transfers
cursor.execute("SELECT app, COUNT(*) FROM django_migrations GROUP BY app")
print('\n=== MIGRATION COUNTS BY APP ===')
for app, count in cursor.fetchall():
    print(f'{app}: {count} migrations')

conn.close()
