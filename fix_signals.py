# Temporarily comment out signals import 
with open('backend/tasks/apps.py', 'r') as f: 
    content = f.read() 
 
# Comment out the signals import 
new_content = content.replace('from . import signals', '# from . import signals  # TEMPORARILY DISABLED') 
 
with open('backend/tasks/apps.py', 'w') as f: 
    f.write(new_content) 
 
print('? Temporarily disabled signals import') 
