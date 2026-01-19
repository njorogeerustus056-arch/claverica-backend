import subprocess, sys

print("=== TESTING manage.py ===")

# Test 1: Basic check
result = subprocess.run([sys.executable, 'manage.py', 'check'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ manage.py check works")
else:
    print(f"❌ manage.py check failed: {result.stderr[:200]}")

# Test 2: Show apps
result = subprocess.run([sys.executable, 'manage.py', 'shell', '-c',
                       "from django.apps import apps; "
                       "print('Total apps:', len(apps.app_configs)); "
                       "backend = [a for a in apps.app_configs if 'backend' in a]; "
                       "print('Backend apps:', len(backend))"],
                       capture_output=True, text=True)
if result.returncode == 0:
    print(f"✅ Shell works:\n{result.stdout}")
else:
    print(f"❌ Shell failed: {result.stderr[:200]}")
