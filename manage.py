#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# ========== FIX PATHS TO PREVENT DUPLICATE MODULES ==========
current_dir = os.path.dirname(os.path.abspath(__file__))
# Remove paths that cause imports without 'backend.' prefix
sys.path = [p for p in sys.path if not p.endswith('backend')]
# Add project root
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# ========== END FIX ==========

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
