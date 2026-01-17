cat > fix_all_issues.py << "EOF"
import os
import sys
import re
import shutil

print("="*70)
print("COMPREHENSIVE FIX FOR DJANGO TASKS APP CONFLICT")
print("="*70)

# ============================================================================
# STEP 1: Fix signals.py - Replace ALL UserTaskItem with UserTask
# ============================================================================
print("\n1. FIXING signals.py...")
signals_path = 'backend/tasks/signals.py'
with open(signals_path, 'r') as f:
    signals_content = f.read()

# Count occurrences
old_count = signals_content.count('UserTaskItem')
print(f"   Found {old_count} occurrences of 'UserTaskItem'")

# Replace ALL occurrences
signals_content = signals_content.replace('UserTaskItem', 'UserTask')

# Write back
with open(signals_path, 'w') as f:
    f.write(signals_content)

new_count = signals_content.count('UserTaskItem')
print(f"   After fix: {new_count} occurrences of 'UserTaskItem' remaining")
print(f"   ✅ Fixed {old_count - new_count} occurrences")

# ============================================================================
# STEP 2: Check for duplicate TaskItem models
# ============================================================================
print("\n2. SEARCHING FOR DUPLICATE TaskItem MODELS...")
matches = []

# Walk through all directories
for root, dirs, files in os.walk('.'):
    # Skip virtual environment and cache
    skip_dirs = ['venv', '__pycache__', '.git', '.pytest_cache', 'node_modules']
    if any(sd in root for sd in skip_dirs):
        continue
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'class TaskItem' in content:
                        matches.append(filepath)
            except:
                pass

print(f"   Found {len(matches)} files with 'class TaskItem':")
for i, match in enumerate(matches, 1):
    print(f"   {i}. {match}")

# ============================================================================
# STEP 3: If duplicates found, rename the non-backend ones
# ============================================================================
if len(matches) > 1:
    print("\n3. HANDLING DUPLICATES...")
    for match in matches:
        # Keep only backend/tasks/models.py
        if 'backend/tasks/models.py' in match.replace('\\', '/'):
            print(f"   KEEPING: {match} (main app)")
            continue
        
        # Rename others
        new_name = match.replace('.py', '_DUPLICATE.py')
        try:
            os.rename(match, new_name)
            print(f"   RENAMED: {match} → {new_name}")
        except Exception as e:
            print(f"   ERROR renaming {match}: {e}")

# ============================================================================
# STEP 4: Check for tasks.py or tasks directory at root level
# ============================================================================
print("\n4. CHECKING FOR ROOT-LEVEL TASKS MODULES...")
root_items = os.listdir('.')
tasks_found = []

for item in root_items:
    if item == 'tasks.py':
        tasks_found.append(item)
    elif item == 'tasks' and os.path.isdir('tasks'):
        tasks_found.append(item)

if tasks_found:
    print(f"   FOUND at root level: {tasks_found}")
    for item in tasks_found:
        new_name = f"{item}_RENAMED"
        try:
            os.rename(item, new_name)
            print(f"   RENAMED: {item} → {new_name}")
        except Exception as e:
            print(f"   ERROR renaming {item}: {e}")
else:
    print("   ✓ No root-level tasks modules found")

# ============================================================================
# STEP 5: Clear all caches
# ============================================================================
print("\n5. CLEARING CACHES...")
cache_dirs = [
    '__pycache__',
    'backend/__pycache__',
    'backend/tasks/__pycache__',
    'backend/tasks/migrations/__pycache__'
]

for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"   ✓ Removed: {cache_dir}")
        except Exception as e:
            print(f"   ✗ Error removing {cache_dir}: {e}")

# Clear Python module cache
modules_to_clear = ['tasks', 'backend.tasks', 'backend.tasks.models', 
                   'backend.tasks.apps', 'backend.tasks.admin', 'backend.tasks.signals']
for module in modules_to_clear:
    if module in sys.modules:
        del sys.modules[module]
        print(f"   ✓ Cleared from sys.modules: {module}")

# ============================================================================
# STEP 6: Verify app configuration
# ============================================================================
print("\n6. VERIFYING APP CONFIGURATION...")
# Check apps.py
apps_py_path = 'backend/tasks/apps.py'
with open(apps_py_path, 'r') as f:
    apps_content = f.read()

# Check if name is 'backend.tasks'
name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", apps_content)
if name_match:
    app_name = name_match.group(1)
    print(f"   App name in apps.py: '{app_name}'")
    
    if app_name != 'backend.tasks':
        print(f"   ⚠️ Should be 'backend.tasks', fixing...")
        apps_content = re.sub(r"name\s*=\s*['\"][^'\"]+['\"]", "name = 'backend.tasks'", apps_content)
        with open(apps_py_path, 'w') as f:
            f.write(apps_content)
        print(f"   ✅ Fixed app name to 'backend.tasks'")
    else:
        print(f"   ✓ App name is correct")
else:
    print("   ❌ Could not find app name in apps.py")

# ============================================================================
# STEP 7: Create a simple test to check imports
# ============================================================================
print("\n7. CREATING IMPORT TEST...")
test_code = '''
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Test 1: Try to import 'tasks' (should fail)
print("Test 1: Importing 'tasks' (should fail)...")
try:
    import tasks
    print(f"   ❌ SUCCESS - This is BAD! Found at: {tasks.__file__}")
except ImportError:
    print("   ✅ FAIL - Good! No root-level tasks module")

# Test 2: Try to import 'backend.tasks' (should work)
print("\\nTest 2: Importing 'backend.tasks' (should work)...")
try:
    import backend.tasks
    print(f"   ✅ SUCCESS - Found at: {backend.tasks.__file__}")
except ImportError as e:
    print(f"   ❌ FAIL - Error: {e}")

# Test 3: Try to import TaskItem model
print("\\nTest 3: Importing TaskItem model...")
try:
    from backend.tasks.models import TaskItem
    print(f"   ✅ SUCCESS - Can import TaskItem")
except ImportError as e:
    print(f"   ❌ FAIL - Error: {e}")
'''

with open('test_imports.py', 'w') as f:
    f.write(test_code)

print("="*70)
print("✅ ALL FIXES APPLIED!")
print("="*70)
print("\nNEXT STEPS:")
print("1. Run: python test_imports.py")
print("2. Then run: python manage.py check")
print("3. If still issues, we may need to rename the entire tasks app")
print("="*70)
EOF