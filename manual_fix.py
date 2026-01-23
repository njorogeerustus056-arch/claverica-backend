import re

with open('backend/settings.py', 'r') as f:
    lines = f.readlines()

# Find and fix the line with receiptsbackend
for i, line in enumerate(lines):
    if 'receiptsbackend' in line:
        print(f'Found typo on line {i}: {line.strip()}')
        
        # Fix it
        lines[i] = line.replace('receiptsbackend', 'receipts')
        print(f'Fixed to: {lines[i].strip()}')
        
        # Write back
        with open('backend/settings.py', 'w') as f:
            f.writelines(lines)
        print('✅ File updated')
        break
else:
    print('✅ No receiptsbackend typo found')
    
    # Check if backend.receipts is missing
    content = ''.join(lines)
    if 'backend.receipts' not in content:
        print('⚠️  backend.receipts is missing from INSTALLED_APPS')
        
        # Find where to add it (after notifications)
        for i, line in enumerate(lines):
            if 'backend.notifications' in line:
                # Insert after this line
                lines.insert(i + 1, '    "backend.receipts",\n')
                print('✅ Added backend.receipts after notifications')
                
                with open('backend/settings.py', 'w') as f:
                    f.writelines(lines)
                break
