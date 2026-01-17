import sys 
try: 
    import django.tasks 
    print('django.tasks module exists') 
    print('Can import Task from it:') 
    from django.tasks.base import Task 
    print('  Task class:', Task) 
except Exception as e: 
    print('Error:', e) 
