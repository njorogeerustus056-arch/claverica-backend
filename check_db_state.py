import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()
from django.db import connection

print("=== DATABASE STATE ===")

# Check django_migrations table
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM django_migrations")
    count = cursor.fetchone()[0]
    print(f"📊 Migrations in DB: {count}")
    
    # Show last 10 migrations
    cursor.execute("SELECT app, name, applied FROM django_migrations ORDER BY applied DESC LIMIT 10")
    print("\nLast 10 migrations:")
    for app, name, applied in cursor.fetchall():
        print(f"  {app}: {name}")

# Check tables count
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema='public'
    """)
    count = cursor.fetchone()[0]
    print(f"\n📊 Total tables in DB: {count}")

# Check our new tables exist
new_tables = [
    'claverica_tasks_clavericatask',
    'claverica_tasks_rewardwithdrawal',
    'claverica_tasks_taskcategory',
    'claverica_tasks_userrewardbalance',
    'escrow_escrow',
    'escrow_escrowlog',
    'kyc_documents',
    'kyc_verifications',
    'crypto_cryptowallet',
    'crypto_cryptotransaction',
    'withdrawal_requests'
]

print("\n🔍 Checking new tables:")
for table in new_tables:
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", [table])
        exists = cursor.fetchone()[0]
        status = "✅" if exists else "❌"
        print(f"{status} {table}")
