import sys 
import os 
print('?? Searching for duplicate tasks module...') 
print() 
print('Modules containing "tasks":') 
for module_name in list(sys.modules.keys()): 
    if 'tasks' in module_name: 
        print(f'  {module_name}') 
print() 
print('Checking Python path for tasks directories:') 
for path in sys.path: 
    if os.path.exists(path): 
        try: 
            items = os.listdir(path) 
            if 'tasks' in items: 
                print(f'Found tasks in: {path}') 
        except: 
            pass 
