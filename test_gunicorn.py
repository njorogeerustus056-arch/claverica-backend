import subprocess
import time
import sys
import os

print("=== Testing Gunicorn ===")

# Start gunicorn
proc = subprocess.Popen(
    [sys.executable, '-m', 'gunicorn', 'backend.wsgi:application', 
     '--bind', '0.0.0.0:8000', '--workers', '1', '--timeout', '30',
     '--access-logfile', '-', '--error-logfile', '-'],
    cwd='backend',
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print(f"Gunicorn started with PID: {proc.pid}")
print("Waiting 5 seconds for server to start...")
time.sleep(5)

try:
    import requests
    response = requests.get('http://127.0.0.1:8000/', timeout=5)
    print(f"✅ Health check: Status {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Could not connect: {e}")

print("\n=== Gunicorn Output ===")
# Try to read some output
try:
    stdout, stderr = proc.communicate(timeout=2)
    print("STDOUT:", stdout[:500] if stdout else "None")
    print("STDERR:", stderr[:500] if stderr else "None")
except subprocess.TimeoutExpired:
    print("Process still running...")

# Kill the process
proc.terminate()
try:
    proc.wait(timeout=5)
    print("Process terminated successfully")
except subprocess.TimeoutExpired:
    proc.kill()
    print("Process killed")
