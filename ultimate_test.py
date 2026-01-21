import os
import sys

# Clean Python path
sys.path = [p for p in sys.path if 'render' in p]
sys.path.insert(0, '/opt/render/project/src')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
try:
    django.setup()
    print('✅ Django setup successful')
    
    # Use the CORRECT import path based on INSTALLED_APPS
    from backend.tasks.models import UserTask
    print(f'✅ UserTask imported: {UserTask.objects.count()} records')
    
    from backend.claverica_tasks.models import TasksClavericatask
    print(f'✅ TasksClavericatask imported: {TasksClavericatask.objects.count()} records')
    
    print('\\n🎉 SUCCESS! All models working with correct import paths.')
    print('\\n📝 IMPORTANT: In your code, use these import paths:')
    print('   from backend.tasks.models import UserTask')
    print('   from backend.claverica_tasks.models import TasksClavericatask')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
