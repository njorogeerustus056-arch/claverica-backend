#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# CRITICAL: Add both current directory and backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')

# Add to Python path so Django can find all modules
sys.path.insert(0, current_dir)      # For finding 'backend' module
sys.path.insert(0, backend_dir)      # For finding apps within backend

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
