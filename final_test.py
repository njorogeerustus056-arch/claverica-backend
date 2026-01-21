import sys
import os

# Remove problematic paths
sys.path = [p for p in sys.path if not p.endswith('/backend')]

# Add only the project root
sys.path.insert(0, '/opt/render/project/src')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
try:
    django.setup()
    print('✅ Django setup successful')
    
    # This should work now
    from tasks.models import UserTask
    print(f'✅ UserTask imported: {UserTask.objects.count()} records')
    
    from claverica_tasks.models import TasksClavericatask
    print(f'✅ TasksClavericatask imported: {TasksClavericatask.objects.count()} records')
    
    print('\\n🎉 ALL MODELS WORKING!')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
