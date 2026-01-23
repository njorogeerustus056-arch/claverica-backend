import subprocess, sys

print("=== CHECKING MIGRATION ERROR ===")

# Run migrate with full output
result = subprocess.run([sys.executable, 'manage.py', 'migrate', '--verbosity', '3'],
                       capture_output=True, text=True)

print("Full error output:")
print(result.stderr)

# Look for specific table errors
if "already exists" in result.stderr:
    print("\n🚨 ERROR: Table already exists!")
    print("Solution: We need to fake migrations or reset")
elif "duplicate key" in result.stderr:
    print("\n🚨 ERROR: Duplicate key constraint!")
    print("Solution: Check for conflicting models")
else:
    print("\n🔍 Unknown error type")
