import os

apps = ['accounts', 'users', 'cards', 'notifications', 'payments', 
        'transactions', 'transfers', 'kyc', 'compliance', 'crypto',
        'escrow', 'withdrawal', 'claverica_tasks', 'tasks', 'receipts', 'tac']

print("Checking __init__.py files...")
for app in apps:
    init_file = f'backend/{app}/__init__.py'
    if os.path.exists(init_file):
        print(f"✅ {app}: has __init__.py")
    else:
        print(f"❌ {app}: MISSING __init__.py")
        # Create it
        with open(init_file, 'w') as f:
            f.write('')
        print(f"   Created __init__.py for {app}")
