import re
with open('backend/settings.py') as f:
    for i, line in enumerate(f, 1):
        if 'receiptsbackend' in line:
            print(f"Line {i}: {line.strip()}")
            break
    else:
        print("Searching for 'backend.receipts'...")
        f.seek(0)
        for i, line in enumerate(f, 1):
            if 'backend.receipts' in line:
                print(f"Line {i}: {line.strip()}")
