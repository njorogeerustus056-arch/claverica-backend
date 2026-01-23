#!/usr/bin/env python3
"""
Patched Django runner that fixes duplicate model issues.
Use this instead of manage.py for production.
"""
import os
import sys

# Fix Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Clear problematic modules
for mod in list(sys.modules.keys()):
    if mod.startswith('users') and not mod.startswith('backend.users'):
        del sys.modules[mod]

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Patch Django BEFORE importing
import django.apps.registry

original_register = django.apps.registry.Apps.register_model

def patched_register(self, app_label, model):
    if app_label == 'users':
        model_name = model._meta.model_name
        if app_label in self.all_models:
            if model_name in self.all_models[app_label]:
                # Skip duplicate - already registered
                return
    return original_register(self, app_label, model)

django.apps.registry.Apps.register_model = patched_register

# Now run Django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    execute_from_command_line(sys.argv)
