import os
import sys

print("=== Gunicorn Diagnostic ===")

# Check if gunicorn is installed
try:
    import gunicorn
    print(f" Gunicorn version: {gunicorn.__version__}")
except ImportError:
    print(" Gunicorn not installed")
    
# Check wsgi.py
print("\n=== Checking wsgi.py ===")
try:
    exec(open('wsgi.py').read())
    print(" wsgi.py executes without error")
except Exception as e:
    print(f" wsgi.py error: {e}")
    
# Check if we can import the WSGI application
print("\n=== Checking WSGI application import ===")
try:
    # Import the module
    import backend.wsgi
    print(" Imported backend.wsgi module")
    
    # Check if 'application' exists
    if hasattr(backend.wsgi, 'application'):
        print(" Found 'application' in backend.wsgi")
        
        # Test if it's callable
        import inspect
        if callable(backend.wsgi.application):
            print(" 'application' is callable (valid WSGI app)")
        else:
            print(" 'application' is not callable")
    else:
        print(" 'application' not found in backend.wsgi")
        
except Exception as e:
    print(f" Error importing backend.wsgi: {e}")
    import traceback
    traceback.print_exc()
