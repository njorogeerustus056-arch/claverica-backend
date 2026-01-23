import re

with open('backend/settings.py', 'r') as f:
    content = f.read()

# Fix the typo: backend.receiptsbackend -> backend.receipts
if 'backend.receiptsbackend' in content:
    content = content.replace("'backend.receiptsbackend'", "'backend.receipts'")
    content = content.replace('"backend.receiptsbackend"', '"backend.receipts"')
    
    with open('backend/settings.py', 'w') as f:
        f.write(content)
    print('✅ Fixed typo: backend.receiptsbackend -> backend.receipts')
else:
    print('✅ No typo found')
