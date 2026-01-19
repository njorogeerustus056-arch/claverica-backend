import subprocess, sys

print("=== FAKING MIGRATIONS ===")

# Apps that we created models for
apps = ['claverica_tasks', 'escrow', 'kyc', 'crypto', 'withdrawal']

for app in apps:
    print(f"\n🔧 Faking migrations for {app}...")
    
    # First check what migrations exist
    result = subprocess.run([sys.executable, 'manage.py', 'showmigrations', app],
                           capture_output=True, text=True)
    print(f"Migrations for {app}:")
    print(result.stdout[:200])
    
    # Fake the migration
    result = subprocess.run([sys.executable, 'manage.py', 'migrate', app, '--fake'],
                           capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {app}: Faked migration")
    else:
        print(f"❌ {app}: Failed - {result.stderr[:100]}")

print("\n📦 Faking all remaining migrations...")
result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--fake'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ All migrations faked!")
else:
    print(f"❌ Fake failed: {result.stderr[:200]}")
