
import sys
sys.path.insert(0, 'D:/FULLSTACK/clavericabackend/backend')

# Direct file test
with open('compliance/services.py', 'r') as f:
    lines = f.readlines()

print("Line 222 from file:", repr(lines[221] if len(lines) > 221 else "NOT FOUND"))

# Test the actual line
exec(