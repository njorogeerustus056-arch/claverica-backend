print("=== FIXING manage.py PROPERLY ===")

# Read the original file
with open('manage.py', 'r') as f:
    content = f.read()

# Find and fix ALL variations
import re

# Replace any execute_from_command_line with extra e's
content = re.sub(r'execute_from_command_linee+', 'execute_from_command_line', content)

# Also check for the exact correct spelling
if 'execute_from_command_line' not in content:
    print("❌ execute_from_command_line still missing!")
    
# Write back
with open('manage.py', 'w') as f:
    f.write(content)

print("✅ manage.py fixed properly!")
print("New content check:")
with open('manage.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[15:25], 16):
        print(f"Line {i}: {line.strip()}")
