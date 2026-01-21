import os
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Add project to path
sys.path.insert(0, '/opt/render/project/src')

import django
django.setup()

try:
    from tasks.models import UserTask
    print(f'✓ UserTask imported successfully: {UserTask.objects.count()} records')
    
    from claverica_tasks.models import TasksClavericatask
    print(f'✓ TasksClavericatask imported successfully: {TasksClavericatask.objects.count()} records')
    
    print('\\n✅ ALL MODELS WORKING!')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
