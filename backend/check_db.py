import sqlite3
import sys

def check_database():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check compliance_transferrequest table
    cursor.execute('PRAGMA table_info(compliance_transferrequest);')
    columns = cursor.fetchall()
    
    print('compliance_transferrequest columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check account column
    account_cols = [c for c in columns if 'account' in c[1].lower()]
    print('\nAccount-related columns:')
    for col in account_cols:
        print(f'  {col[1]} ({col[2]})')
    
    # Check if notifications_notification table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'notifications_%';")
    tables = cursor.fetchall()
    
    print('\nAll notifications tables:')
    for table in tables:
        print(f'  {table[0]}')
    
    # Check notifications_notification columns if exists
    cursor.execute("PRAGMA table_info('notifications_notification');")
    columns = cursor.fetchall()
    
    if columns:
        print('\nnotifications_notification columns:')
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
    else:
        print('\nnotifications_notification table does not exist')
    
    # Check migration status
    cursor.execute("SELECT * FROM django_migrations WHERE app='notifications';")
    migrations = cursor.fetchall()
    print('\nNotifications migrations:')
    for mig in migrations:
        print(f'  {mig[1]} ({mig[2]}) - Applied: {mig[3]}')
    
    conn.close()

if __name__ == '__main__':
    check_database()