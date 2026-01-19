import os
path = "backend/transfers/migrations/0001_initial.py"
with open(path, 'r') as f:
    content = f.read()

# Remove compliance_module dependency
import re
new_content = re.sub(r"\('compliance_module', '0001_initial'\),\s*", "", content)

with open(path, 'w') as f:
    f.write(new_content)

print("Fixed transfers migration")
