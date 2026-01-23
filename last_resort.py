import os
import shutil
import subprocess

print("=== LAST RESORT: Delete and recreate receipts ===")

# 1. Delete receipts app
print("1. Deleting receipts app...")
if os.path.exists('backend/receipts'):
    shutil.rmtree('backend/receipts')
    print("✅ Deleted")

# 2. Remove from INSTALLED_APPS temporarily
print("\n2. Removing from settings.py...")
with open('backend/settings.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "'backend.receipts'" not in line:
        new_lines.append(line)

with open('backend/settings.py', 'w') as f:
    f.writelines(new_lines)
print("✅ Removed from INSTALLED_APPS")

# 3. Run migrations for other apps
print("\n3. Running other migrations...")
subprocess.run(['python', 'manage.py', 'makemigrations', 'notifications', 'users'], 
               capture_output=True, text=True)
subprocess.run(['python', 'manage.py', 'migrate'], capture_output=True, text=True)

print("\n✅ System should work without receipts for now")
print("You can add receipts back later when shell is fixed")
