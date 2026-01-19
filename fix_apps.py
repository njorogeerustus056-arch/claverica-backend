import os

apps = ['escrow', 'kyc', 'compliance', 'crypto', 'receipts', 
        'claverica_tasks', 'tasks', 'withdrawal', 'tac']

for app in apps:
    app_dir = f'backend/{app}'
    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)
        print(f'📁 Created: {app_dir}')
        
        # Create __init__.py
        open(f'{app_dir}/__init__.py', 'w').close()
        
        # Create apps.py
        with open(f'{app_dir}/apps.py', 'w') as f:
            f.write(f'''from django.apps import AppConfig

class {app.title().replace('_', '')}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.{app}'
    verbose_name = '{app.replace('_', ' ').title()}'
''')
        
        # Create models.py placeholder
        with open(f'{app_dir}/models.py', 'w') as f:
            f.write('# Models will be auto-generated\n')
        
        # Create admin.py
        with open(f'{app_dir}/admin.py', 'w') as f:
            f.write('# Admin will be configured later\n')
        
        print(f'   ✅ Created files for {app}')
    else:
        print(f'📁 Exists: {app_dir}')
