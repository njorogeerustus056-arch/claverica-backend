# cleanup.py
"""
Clean up all old test files
"""

import os
import shutil

# Files to KEEP (only these)
KEEP_FILES = [
    'test_final.py',          # Our new final test file
    'models.py',
    'views.py',
    'serializers.py',
    'services.py',
    'signals.py',
    'urls.py',
    'admin.py',
    'apps.py',
    '__init__.py',
    'requirements.txt',
    'README.md',
    'db.sqlite3',
    'migrations/',
    'management/',
]

# Files to DELETE (all test files except our new one)
DELETE_FILES = [
    'test_cards_application.py',
    'test_cards_simple.py',
    'test_cards_working.py',
    'test_consolidated.py',
    'test_correct.py',
    'test_final_fixed.py',
    'test_fixed.py',
    'test_fixed_final.py',
    'test_proper.py',
    'test_with_db.py',
    'tests.py',
    'run_tests.py',
    'run_tests_properly.py',
    'check_backend.py',
    'diagnostic.py',
    'discover_project.py',
    'explore_project.py',
    'list_backend.py',
    'user_diagnostic.py',
    'urls.py.backup',
]

print("=" * 80)
print("CLEANUP SCRIPT")
print("=" * 80)

current_dir = os.getcwd()
print(f"Current directory: {current_dir}")

# Show files that will be deleted
print("\n⚠️  Files that will be DELETED:")
for f in DELETE_FILES:
    if os.path.exists(os.path.join(current_dir, f)):
        print(f"  - {f}")

print("\n✅ Files that will be KEPT:")
for f in KEEP_FILES:
    if os.path.exists(os.path.join(current_dir, f)):
        print(f"  - {f}")

# Ask for confirmation
response = input("\nAre you sure you want to delete these files? (yes/no): ")

if response.lower() == 'yes':
    deleted_count = 0
    for f in DELETE_FILES:
        file_path = os.path.join(current_dir, f)
        if os.path.exists(file_path):
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                print(f"Deleted: {f}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {f}: {e}")
    
    print(f"\n✅ Cleanup complete! Deleted {deleted_count} files.")
    print("\nNow you have a clean directory with only essential files.")
    print("Run your tests with: python test_final.py")
else:
    print("\n⚠️  Cleanup cancelled. No files were deleted.")
    print("\nYou can still run the clean tests with: python test_final.py")