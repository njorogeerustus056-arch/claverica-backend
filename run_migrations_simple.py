import subprocess
import sys

apps = ['claverica_tasks', 'escrow', 'kyc', 'crypto', 'withdrawal']

print('🔧 Running migrations...')

# First make migrations
for app in apps:
    print(f'Making migrations for {app}...')
    result = subprocess.run(
        [sys.executable, 'manage.py', 'makemigrations', app],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        if 'No changes' in result.stdout:
            print(f'  ⚠️  No changes for {app}')
        else:
            print(f'  ✅ Created migrations for {app}')
    else:
        print(f'  ❌ Error for {app}: {result.stderr[:100]}')

# Then migrate
print('\nApplying migrations...')
result = subprocess.run(
    [sys.executable, 'manage.py', 'migrate'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print('✅ All migrations applied!')
else:
    print(f'❌ Migration error: {result.stderr[:200]}')
