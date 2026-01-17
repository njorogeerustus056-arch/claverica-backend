echo print("STEP 1: Checking apps.py configuration") > step1_check_apps.py
echo print("="*50) >> step1_check_apps.py
echo. >> step1_check_apps.py
echo with open('backend/tasks/apps.py', 'r') as f: >> step1_check_apps.py
echo     content = f.read() >> step1_check_apps.py
echo. >> step1_check_apps.py
echo print("Current apps.py content:") >> step1_check_apps.py
echo print("-"*40) >> step1_check_apps.py
echo for line in content.split('\n'): >> step1_check_apps.py
echo     if 'name' in line or 'label' in line or 'class' in line: >> step1_check_apps.py
echo         print(f"  {line}") >> step1_check_apps.py
echo print("-"*40) >> step1_check_apps.py