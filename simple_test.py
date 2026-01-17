import sys 
sys.path.insert(0, '.') 
print("1. Trying to import 'tasks'...") 
try: 
    import tasks 
    print("   SUCCESS - found tasks module") 
    print("   Location:", tasks.__file__) 
except ImportError: 
    print("   FAILED - no tasks module") 
 
print("2. Trying to import 'backend.tasks'...") 
try: 
    import backend.tasks 
    print("   SUCCESS - found backend.tasks module") 
    print("   Location:", backend.tasks.__file__) 
except ImportError as e: 
    print("   FAILED - error:", e) 
