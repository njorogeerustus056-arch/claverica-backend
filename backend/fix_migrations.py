import sqlite3
import datetime
import os
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django
django.setup()

db_path = settings.DATABASES['default']['NAME']
print(f'Database: {db_path}')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('\n=== FIXING MIGRATION DEPENDENCIES ===')

# Show current state
cursor.execute('SELECT app, name FROM django_migrations ORDER BY id')
print('Current migrations:')
for app, name in cursor.fetchall():
    print(f'  {app}.{name}')

# Clear all migrations (nuclear option for clean start)
print('\nClearing migration history...')
cursor.execute('DELETE FROM django_migrations')

# Add migrations in correct dependency order
now = datetime.datetime.now().isoformat()
migrations = [
    ('accounts', '0001_initial'),
    ('users', '0001_initial'), 
    ('transfers', '0001_initial'),
    # Add any other apps here
]

for app, name in migrations:
    cursor.execute(
        'INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, ?)',
        (app, name, now)
    )
    print(f'  Added: {app}.{name}')

conn.commit()
print('\n Migration history reset in correct order!')
print('\nNow run: python manage.py migrate --fake')

conn.close()
