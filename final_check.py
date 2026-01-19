import subprocess, sys

print("=== FINAL CHECK ===")

# 1. Check Django
result = subprocess.run([sys.executable, 'manage.py', 'check'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Django check passed")
else:
    print(f"❌ Django check: {result.stderr[:200]}")

# 2. Show apps
result = subprocess.run([sys.executable, 'manage.py', 'shell', '-c',
                       "from django.apps import apps; "
                       "backend = [a for a in apps.app_configs if 'backend' in a]; "
                       "print(f'Backend apps: {len(backend)}'); "
                       "for app in sorted(backend): print(f'  - {app}')"],
                       capture_output=True, text=True)
if result.returncode == 0:
    print(f"\n{result.stdout}")
else:
    print(f"❌ Shell error: {result.stderr[:200]}")
