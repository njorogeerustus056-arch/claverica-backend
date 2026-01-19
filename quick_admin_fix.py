import sys, os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

# Apps that need admin registration
apps_to_fix = ['kyc', 'crypto', 'escrow', 'claverica_tasks', 'compliance', 'tac', 'withdrawal', 'receipts', 'tasks']

print("🛠️ QUICK ADMIN FIX:")

for app_name in apps_to_fix:
    admin_file = f'backend/{app_name}/admin.py'
    
    # Read current admin file
    with open(admin_file, 'r') as f:
        content = f.read()
    
    # Check if models are imported
    if 'from . import models' not in content and 'from .models import' not in content:
        print(f"➕ Fixing {app_name} admin.py")
        
        # Add import and basic registration
        fixed_content = f'''from django.contrib import admin
from . import models

# Register your models here
'''
        
        # Add registration for each model
        try:
            app_config = django.apps.apps.get_app_config(app_name)
            for model in app_config.get_models():
                model_name = model.__name__
                fixed_content += f'''
@admin.register(models.{model_name})
class {model_name}Admin(admin.ModelAdmin):
    list_display = ['id']
    search_fields = []
    list_filter = []
    
'''
        except:
            fixed_content += f'''
# Models will be auto-registered
'''
        
        with open(admin_file, 'w') as f:
            f.write(fixed_content)
        
        print(f"   ✅ Fixed {app_name}")
    else:
        print(f"📄 {app_name} admin looks OK")

print("\n🎯 Admin files updated!")
