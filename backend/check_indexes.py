#!/usr/bin/env python
"""
🎯 CHECK DATABASE INDEXES
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()

from django.db import connection

print("🔍 CHECKING DATABASE INDEXES")
print("=" * 60)

with connection.cursor() as cursor:
    # Get all indexes
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index'")
    indexes = cursor.fetchall()
    
    print(f"\n📋 Found {len(indexes)} total indexes in database:")
    
    # Filter for notification indexes
    notification_indexes = []
    for idx in indexes:
        name, tbl_name, sql = idx
        if 'notification' in name.lower() or 'notifications_' in tbl_name:
            notification_indexes.append(idx)
    
    print(f"\n🎯 {len(notification_indexes)} notification-related indexes:")
    for name, tbl_name, sql in notification_indexes:
        print(f"   📌 {name} (table: {tbl_name})")
        if sql:
            print(f"      SQL: {sql[:100]}...")

# Check migration state
from django.db.migrations.recorder import MigrationRecorder
migration_recorder = MigrationRecorder(connection)
applied = migration_recorder.applied_migrations()

print(f"\n📦 Applied migrations for 'notifications':")
for app, name in applied:
    if app == 'notifications':
        print(f"   ✅ {name}")

print("\n" + "=" * 60)
print("✅ INDEX CHECK COMPLETE")