#!/usr/bin/env python3
import os
import subprocess

print("=== FIXING NOTIFICATIONS ===")

# 1. Create MINIMAL admin.py
admin_content = '''from django.contrib import admin
from .models import (
    NotificationNew as Notification,
    NotificationPreference,
    NotificationTemplate,
    NotificationLog,
    NotificationDevice
)

@admin.register(NotificationNew)
class NotificationAdmin(admin.ModelAdmin):
    pass

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    pass

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    pass

@admin.register(NotificationDevice)
class NotificationDeviceAdmin(admin.ModelAdmin):
    pass
'''

with open('backend/notifications/admin.py', 'w') as f:
    f.write(admin_content)
print("✅ Created admin.py")

# 2. Clear cache
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc'):
            os.remove(os.path.join(root, file))
    if '__pycache__' in dirs:
        import shutil
        shutil.rmtree(os.path.join(root, '__pycache__'))
print("✅ Cleared cache")

# 3. Try migrations
print("\n=== RUNNING MIGRATIONS ===")
result = subprocess.run(['python', 'manage.py', 'makemigrations', 'notifications'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ MIGRATIONS SUCCESS!")
    print(result.stdout[-300:])
else:
    print("❌ MIGRATIONS FAILED")
    print("Error:", result.stderr[-300:] if result.stderr else "No error")
