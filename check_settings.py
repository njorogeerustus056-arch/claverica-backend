import re

with open('backend/settings.py', 'r') as f:
    content = f.read()

# Find INSTALLED_APPS section
match = re.search(r'INSTALLED_APPS\s*=\s*\[(.*?)\]', content, re.DOTALL)
if match:
    print('=== INSTALLED_APPS SECTION ===')
    apps_section = match.group(1)
    
    # Extract all app entries
    apps = re.findall(r'["\']([^"\']+)["\']', apps_section)
    
    print(f'Found {len(apps)} apps:')
    
    # Group by type
    backend_apps = []
    third_party = []
    
    for app in apps:
        if app.startswith('backend.'):
            backend_apps.append(app)
        else:
            third_party.append(app)
    
    print(f'\n📦 Backend apps ({len(backend_apps)}):')
    for app in sorted(backend_apps):
        print(f'  {app}')
    
    # Check for receipt-related issues
    print('\n🔍 Checking for receipt issues...')
    receipt_variants = [a for a in backend_apps if 'receipt' in a]
    if receipt_variants:
        print(f'Found receipt variants: {receipt_variants}')
    else:
        print('No receipt apps found!')
        
    # Check for duplicates
    from collections import Counter
    dupes = [app for app, count in Counter(backend_apps).items() if count > 1]
    if dupes:
        print(f'\n🚨 DUPLICATES FOUND: {dupes}')
    
else:
    print('Could not find INSTALLED_APPS')
