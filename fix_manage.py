import os

print("=== FIXING manage.py ===")
with open('manage.py', 'r') as f:
    lines = f.readlines()

# Find and fix the error
for i, line in enumerate(lines):
    if 'execute_from_command_lin' in line:
        print(f"Found error on line {i+1}: {line.strip()}")
        lines[i] = line.replace('execute_from_command_lin', 'execute_from_command_line')
        print(f"Fixed to: {lines[i].strip()}")

# Write back
with open('manage.py', 'w') as f:
    f.writelines(lines)

print("✅ manage.py fixed!")
