import re
with open('backend/settings.py') as f:
    content = f.read()

# The bug: 'backend.receiptsbackend.payments' should be two separate apps
if 'backend.receiptsbackend.payments' in content:
    print("Fixing: receiptsbackend.payments")
    # Replace with two separate apps
    content = content.replace(
        '"backend.receiptsbackend.payments"',
        '"backend.receipts",\n    "backend.payments"'
    )
    # Also check single quotes version
    content = content.replace(
        "'backend.receiptsbackend.payments'",
        "'backend.receipts',\n    'backend.payments'"
    )
    with open('backend/settings.py', 'w') as f:
        f.write(content)
    print("✅ Fixed!")
else:
    print("✅ No receiptsbackend.payments found")
