import subprocess, sys

print("=== RUNNING MIGRATIONS ===")

# Apps that need models
apps = ['claverica_tasks', 'escrow', 'kyc', 'crypto', 'withdrawal']

for app in apps:
    print(f"\n🔧 Making migrations for {app}...")
    result = subprocess.run([sys.executable, 'manage.py', 'makemigrations', app],
                           capture_output=True, text=True)
    if result.returncode == 0:
        if 'No changes' in result.stdout:
            print(f"  ✅ {app}: No changes needed")
        else:
            print(f"  ✅ {app}: Created migrations")
    else:
        print(f"  ❌ {app}: Failed - {result.stderr[:100]}")

print("\n📦 Applying all migrations...")
result = subprocess.run([sys.executable, 'manage.py', 'migrate'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ All migrations applied!")
else:
    print(f"❌ Migrations failed: {result.stderr[:200]}")
