import sqlite3
import os

def check_all_tables():
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist!")
        return
    
    print(f"Database size: {os.path.getsize(db_path)} bytes")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\nTotal tables found: {len(tables)}")
    print("All tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check specific tables
    tables_to_check = [
        'compliance_transferrequest',
        'notifications_notification',
        'django_migrations',
        'auth_user',
        'accounts_account'
    ]
    
    print("\nChecking specific tables:")
    for table_name in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        exists = cursor.fetchone()[0]
        if exists:
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print(f"\n{table_name} ({len(columns)} columns):")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        else:
            print(f"\n{table_name}: DOES NOT EXIST")
    
    conn.close()

if __name__ == '__main__':
    check_all_tables()