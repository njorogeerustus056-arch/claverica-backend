import os
import sys

print("Current directory:", os.getcwd())
print("Files in current directory:", os.listdir('.'))

# Try to import backend module
try:
    import backend
    print("✅ Successfully imported 'backend' module")
    print("Backend module location:", backend.__file__)
except ImportError as e:
    print(f"❌ Failed to import 'backend': {e}")
    
# Try to import backend.settings specifically
try:
    import backend.settings
    print("✅ Successfully imported 'backend.settings'")
except ImportError as e:
    print(f"❌ Failed to import 'backend.settings': {e}")
    
# Check Python path
print("\nPython path:")
for path in sys.path:
    print(f"  - {path}")
