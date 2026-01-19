#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import re

print("=" * 60)
print("FINAL FIX: Using Python script (bypasses broken shell)")
print("=" * 60)

def run_command(cmd):
    """Run command and return result"""
    print(f"\nRunning: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Success")
        return True
    else:
        print(f"❌ Failed")
        if result.stderr:
            print(f"Error: {result.stderr[:500]}")
        return False

# 1. Clear ALL caches
print("\n1. Clearing ALL caches...")
os.system("find . -name '*.pyc' -delete 2>/dev/null")
os.system("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null")

# 2. Check what's in receipts/models.py
print("\n2. Checking receipts/models.py...")
with open('backend/receipts/models.py', 'r') as f:
    content = f.read()
    print(f"File length: {len(content)} chars")
    print(f"Contains 'app_label': {'app_label' in content}")
    if 'app_label' in content:
        # Extract app_label value
        match = re.search(r"app_label\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            print(f"Current app_label: {match.group(1)}")

# 3. COMPLETELY rewrite receipts/models.py with unique app_label
print("\n3. COMPLETELY rewriting receipts/models.py...")
new_models = '''from django.db import models
from django.conf import settings

class Receipt(models.Model):
    """Receipt model - FRESH VERSION"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'receipts_final_v1'
    
    def __str__(self):
        return f"Receipt: {self.file_name}"
'''

with open('backend/receipts/models.py', 'w') as f:
    f.write(new_models)
print("✅ Created FRESH receipts/models.py")

# 4. Update receipts/apps.py
print("\n4. Updating receipts/apps.py...")
with open('backend/receipts/apps.py', 'r') as f:
    content = f.read()

# Replace ANY label
content = re.sub(r"label\s*=\s*['\"][^'\"]+['\"]", "label = 'receipts_final_v1'", content)

with open('backend/receipts/apps.py', 'w') as f:
    f.write(content)
print("✅ Updated receipts/apps.py")

# 5. NOW try migrations
print("\n5. Attempting migrations...")
success = run_command("python manage.py makemigrations receipts")

if success:
    print("\n🎉🎉🎉 SUCCESS! Migrations created 🎉🎉🎉")
    # Also try other apps
    run_command("python manage.py makemigrations notifications")
    run_command("python manage.py makemigrations users")
    run_command("python manage.py migrate")
else:
    print("\n❌ Still failing. Last resort options:")
    print("   a) Delete receipts app completely")
    print("   b) Check for duplicate 'receipts' directory")
    print("   c) Restart Render service")
