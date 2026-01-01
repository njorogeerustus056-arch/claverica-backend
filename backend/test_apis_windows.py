# test_apis_windows.py
import os
import sys
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

print("="*60)
print("API URLS AVAILABLE IN YOUR BACKEND")
print("="*60)

# Run show_urls command
from django.core.management import call_command
from io import StringIO

# Capture output
output = StringIO()
call_command('show_urls', stdout=output)
urls_output = output.getvalue()

# Filter and display API urls
print("\nAPI Endpoints:")
print("-" * 60)
for line in urls_output.split('\n'):
    if '/api/' in line:
        parts = line.split()
        if len(parts) >= 3:
            url = parts[0]
            view = parts[1]
            name = parts[2] if len(parts) > 2 else ''
            print(f"{url:<40} -> {view:<30} ({name})")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("\n✅ Your backend has these API categories:")
print("   1. /api/receipts/    - Receipt management")
print("   2. /api/tasks/       - Tasks & rewards system")
print("   3. /api/transactions/- Transaction management")
print("   4. /api/user/profile/- User profile")

print("\n⚠️  Other apps might have URLs configured via:")
print("   - Django REST Framework routers")
print("   - API versioning")
print("   - Different URL prefixes")

print("\n🚀 To see ALL URLs including admin, auth, etc.:")
print("   python manage.py show_urls")