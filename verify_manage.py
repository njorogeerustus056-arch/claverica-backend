print("=== VERIFYING manage.py ===")
with open('manage.py', 'r') as f:
    lines = f.readlines()
    
# Check lines 19 and 24
for i in [18, 23]:  # Python is 0-indexed
    if i < len(lines):
        line = lines[i].strip()
        print(f"Line {i+1}: {line}")
        if 'execute_from_command_line' in line:
            if line.endswith('e') and not line.endswith('line'):
                print(f"  ❌ Still has extra 'e': {line[-10:]}")
            else:
                print(f"  ✅ Correct!")
        else:
            print(f"  ❌ Missing execute_from_command_line")

# Test import
import subprocess, sys
result = subprocess.run([sys.executable, 'manage.py', '--version'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print(f"✅ manage.py works! Version: {result.stdout.strip()}")
else:
    print(f"❌ manage.py still broken: {result.stderr[:100]}")
