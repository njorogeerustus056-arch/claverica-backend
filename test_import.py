
import sys
print("Test 1: Direct import of backend.tasks.models")
try:
    from backend.tasks import models as backend_models
    print("  SUCCESS")
except Exception as e:
    print(f"  ERROR: {e}")

print("\nTest 2: Try to import backend.claverica_tasks.models")
try:
    # Prevent Python from finding backend/tasks as tasks
    if 'backend' in sys.path:
        sys.path.remove('backend')
    
    import backend.claverica_tasks.models
    print("  SUCCESS - found separate tasks.models")
except ImportError as e:
    print(f"  ImportError (expected): {e}")
except Exception as e:
    print(f"  ERROR: {e}")
