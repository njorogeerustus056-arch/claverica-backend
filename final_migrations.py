import subprocess, sys

print("=== FINAL MIGRATIONS ===")

# First make migrations for newly created models
new_apps = ['tasks', 'compliance', 'tac', 'receipts']

for app in new_apps:
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

# Now try to migrate
print("\n📦 Applying ALL migrations...")
result = subprocess.run([sys.executable, 'manage.py', 'migrate'],
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ ALL MIGRATIONS SUCCESSFUL!")
    print("\n🚀 CLAVERICA PLATFORM IS READY!")
else:
    print(f"\n❌ Migration failed. Trying with --fake-initial...")
    
    result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--fake-initial'],
                           capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Migrations applied with --fake-initial")
    else:
        print(f"❌ Still failed: {result.stderr[:200]}")
        
        # Last resort: show migration plan
        print("\n🔍 Migration plan:")
        result = subprocess.run([sys.executable, 'manage.py', 'showmigrations'],
                               capture_output=True, text=True)
        print(result.stdout)
