import os

apps = [
    'accounts', 'users', 'cards', 'notifications', 'payments',
    'transactions', 'transfers', 'kyc', 'compliance', 'crypto',
    'escrow', 'withdrawal', 'claverica_tasks', 'tasks', 'receipts', 'tac'
]

print("🛠️ CREATING ADMIN FILES:")

for app in apps:
    admin_file = f'backend/{app}/admin.py'
    
    # Check if admin file exists and has content
    if os.path.exists(admin_file):
        with open(admin_file, 'r') as f:
            content = f.read()
        
        # If file is empty or just placeholder
        if len(content.strip()) < 50 or '# Admin' in content:
            print(f"➕ Creating admin for {app}")
            
            # Create basic admin
            admin_content = f'''from django.contrib import admin
from . import models

# Register {app.title()} models here
'''
            
            # Try to import models and add them
            try:
                import sys
                sys.path.insert(0, '.')
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
                import django
                django.setup()
                
                app_config = django.apps.apps.get_app_config(app)
                for model in app_config.get_models():
                    model_name = model.__name__
                    admin_content += f'''
@admin.register(models.{model_name})
class {model_name}Admin(admin.ModelAdmin):
    list_display = ['id']
    list_filter = []
    search_fields = []
    
'''
            except:
                # Generic fallback
                admin_content += f'''
# Add your model registrations here
# Example:
# @admin.register(models.YourModel)
# class YourModelAdmin(admin.ModelAdmin):
#     pass
'''
            
            with open(admin_file, 'w') as f:
                f.write(admin_content)
            
            print(f"  ✅ Created admin for {app}")
        else:
            print(f"📄 {app} admin already exists")
    else:
        print(f"❌ {app} admin file missing")
        # Create empty admin file
        with open(admin_file, 'w') as f:
            f.write(f'# {app.title()} admin configuration\n')
        print(f"  ✅ Created empty admin for {app}")

print("\n🎯 All admin files ready!")
