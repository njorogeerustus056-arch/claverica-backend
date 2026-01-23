import re

with open('backend/settings.py', 'r') as f:
    lines = f.readlines()

print('Searching for receipt-related typos...')
for i, line in enumerate(lines, 1):
    if 'receipt' in line.lower():
        print(f'Line {i}: {line.strip()}')
        # Check for common typos
        if 'receiptsbackend' in line:
            print(f'  ⚠️  FOUND TYPO: receiptsbackend')
