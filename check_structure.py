import sqlite3
import os

def check_table_structure():
    db_path = '../db.sqlite3'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check compliance_transferrequest columns
    cursor.execute("PRAGMA table_info(compliance_transferrequest);")
    columns = cursor.fetchall()
    
    print("compliance_transferrequest columns:")
    for col in columns:
        print(f"  {col[0]}: {col[1]} ({col[2]}) - PK: {col[5]}")
    
    # Check foreign keys
    cursor.execute("PRAGMA foreign_key_list(compliance_transferrequest);")
    fks = cursor.fetchall()
    
    print("\nForeign keys:")
    for fk in fks:
        print(f"  From: {fk[3]} -> To: {fk[2]}.{fk[4]}")
    
    # Check existing data
    cursor.execute("SELECT id, account_id, reference FROM compliance_transferrequest LIMIT 5;")
    rows = cursor.fetchall()
    
    print("\nSample data (first 5 rows):")
    for row in rows:
        print(f"  ID: {row[0]}, Account ID: {row[1]}, Reference: {row[2]}")
    
    conn.close()

if __name__ == '__main__':
    check_table_structure()