import re

with open('backend/settings.py', 'r') as f:
    content = f.read()

# List of possible typos and their fixes
typos = {
    'backend.receiptsbackend': 'backend.receipts',
    '"backend.receiptsbackend"': '"backend.receipts"',
    "'backend.receiptsbackend'": "'backend.receipts'",
    'backend.receipts,backend': 'backend.receipts',
    'backend.receipts backend': 'backend.receipts',
}

fixed = False
for typo, fix in typos.items():
    if typo in content:
        content = content.replace(typo, fix)
        print(f'✅ Fixed: {typo} -> {fix}')
        fixed = True

if fixed:
    with open('backend/settings.py', 'w') as f:
        f.write(content)
    print('✅ Settings file updated')
else:
    print('✅ No typos found')
    
# Also check for malformed lines
if 'backend.receipts' in content:
    # Find how it appears in INSTALLED_APPS
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'backend.receipts' in line and '#' not in line:
            print(f'\nReceipts line {i}: {line.strip()}')
            # Check if it's properly quoted
            if not ('"' in line or "'" in line):
                print('  ⚠️  Line might be malformed')
