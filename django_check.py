import sys 
sys.path.insert(0, '.') 
import django 
import os 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') 
django.setup() 
from django.apps import apps 
print('Registered apps:') 
for app in apps.get_app_configs(): 
    print(f'  {app.name}: {app.module}') 
