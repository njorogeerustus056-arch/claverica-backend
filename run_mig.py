import subprocess, sys
print("Running makemigrations...")
result = subprocess.run([sys.executable, 'manage.py', 'makemigrations'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Makemigrations OK")
else:
    print(f"❌ Makemigrations failed: {result.stderr[:100]}")

print("\nRunning migrate...")
result = subprocess.run([sys.executable, 'manage.py', 'migrate'],
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Migrate OK")
else:
    print(f"❌ Migrate failed: {result.stderr[:100]}")
