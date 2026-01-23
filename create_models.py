import os

apps = ['escrow', 'kyc', 'crypto', 'claverica_tasks', 'withdrawal']

for app in apps:
    model_file = f'backend/{app}/models.py'
    if os.path.exists(model_file) and os.path.getsize(model_file) < 50:
        # File is small or empty, create basic model
        with open(model_file, 'w') as f:
            f.write(f'''from django.db import models

class {app.title().replace('_', '')}(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = '{app}_placeholder'
''')
        print(f"✅ Created model for {app}")
    else:
        print(f"📄 {app} model exists")
