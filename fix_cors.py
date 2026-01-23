import sys
import os

# Add to path
sys.path.append('.')

# Read settings.py
with open('backend/settings.py', 'r') as f:
    content = f.read()

# Check current state
print("Current settings analysis:")
print("DEBUG = True" if "DEBUG = True" in content else "DEBUG = False (probably)")
print("CORS_ALLOW_ALL_ORIGINS = DEBUG" in content)

# Fix 1: Make CORS_ALLOW_ALL_ORIGINS = True
if "CORS_ALLOW_ALL_ORIGINS = DEBUG" in content:
    content = content.replace(
        "CORS_ALLOW_ALL_ORIGINS = DEBUG",
        "CORS_ALLOW_ALL_ORIGINS = True  # Changed from DEBUG for frontend development"
    )
    print("✅ Fixed CORS_ALLOW_ALL_ORIGINS")

# Fix 2: Add CORS_ALLOW_CREDENTIALS = True
if "CORS_ALLOW_CREDENTIALS = " not in content:
    # Find where to add it (after CORS_ALLOW_ALL_ORIGINS)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "CORS_ALLOW_ALL_ORIGINS" in line:
            lines.insert(i+1, "CORS_ALLOW_CREDENTIALS = True")
            break
    content = '\n'.join(lines)
    print("✅ Added CORS_ALLOW_CREDENTIALS = True")

# Fix 3: Ensure localhost is in CORS_ALLOWED_ORIGINS
if 'http://localhost:5173' not in content:
    # Find CORS_ALLOWED_ORIGINS section
    import re
    pattern = r'CORS_ALLOWED_ORIGINS\s*=\s*\[([^\]]+)\]'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # Add localhost to the list
        new_origins = match.group(1).strip() + '\n    "http://localhost:5173",\n    "http://127.0.0.1:5173",'
        content = content[:match.start(1)] + new_origins + content[match.end(1):]
        print("✅ Added localhost to CORS_ALLOWED_ORIGINS")

# Write back
with open('backend/settings.py', 'w') as f:
    f.write(content)

print("✅ CORS settings updated!")
print("Restart the Django server for changes to take effect.")
