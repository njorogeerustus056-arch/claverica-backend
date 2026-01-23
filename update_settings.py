import re

with open('backend/settings.py', 'r') as f:
    content = f.read()

# Find INSTALLED_APPS section
match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.DOTALL)
if match:
    installed_content = match.group(1)
    
    # Apps to add (in logical order)
    apps_to_add = [
        'backend.kyc',
        'backend.compliance', 
        'backend.tac',
        'backend.crypto',
        'backend.escrow',
        'backend.withdrawal',
        'backend.claverica_tasks',
        'backend.tasks',
        'backend.receipts'
    ]
    
    # Check which apps are missing
    missing = []
    for app in apps_to_add:
        if f'"{app}"' not in installed_content:
            missing.append(app)
    
    if missing:
        # Add after the last existing backend app
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'backend.notifications' in line:
                insert_line = i + 1
                break
        
        # Insert missing apps
        insert_text = '\n    ' + ',\n    '.join([f'"{app}"' for app in missing])
        lines.insert(insert_line, insert_text)
        
        with open('backend/settings.py', 'w') as f:
            f.write('\n'.join(lines))
        
        print(f'✅ Added {len(missing)} apps to INSTALLED_APPS:')
        for app in missing:
            print(f'  - {app}')
    else:
        print('✅ All apps already in INSTALLED_APPS')
else:
    print('❌ Could not find INSTALLED_APPS')
