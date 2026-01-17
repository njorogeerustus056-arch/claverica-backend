# Fix script for tasks models 
import re 
 
with open('backend/tasks/models.py', 'r') as f: 
    content = f.read() 
 
# Find Task model 
task_start = content.find('class Task(models.Model):') 
if task_start != -1: 
    # Find where Task class ends 
    # Look for next class definition or end of file 
    next_class = content.find('class ', task_start + 1) 
    if next_class == -1: 
        next_class = len(content) 
 
    task_content = content[task_start:next_class] 
 
    # Check if it has Meta class 
    if 'class Meta:' in task_content: 
        # Add app_label to Meta 
        new_task = task_content.replace('class Meta:', 'class Meta:\n        app_label = \"claverica_tasks\"') 
    else: 
        # Add Meta class with app_label 
        # Find where to insert it (after fields, before next method/class) 
        lines = task_content.split('\n') 
        new_lines = [] 
        for line in lines: 
            new_lines.append(line) 
            if line.strip() and not line.startswith(' ') and 'def ' not in line and 'class ' not in line and line != lines[0]: 
                # Insert Meta here 
                new_lines.append('    class Meta:') 
                new_lines.append('        app_label = \"claverica_tasks\"') 
                new_lines.append('') 
        new_task = '\n'.join(new_lines) 
 
    # Replace in original content 
    new_content = content[:task_start] + new_task + content[next_class:] 
 
    with open('backend/tasks/models.py', 'w') as f: 
        f.write(new_content) 
 
    print('? Added app_label to Task model') 
else: 
    print('? Could not find Task model') 
