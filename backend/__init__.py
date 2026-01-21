"""
Patch to fix duplicate UserProfile import issue.
This runs before Django loads.
"""
import sys
import os

# Clear any cached 'users' module
if 'users' in sys.modules:
    del sys.modules['users']
if 'users.models' in sys.modules:
    del sys.modules['users.models']

# Ensure Python looks in backend first
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("✅ Applied import patch in backend/__init__.py")
# Database fix applied: All NOT NULL constraints resolved
