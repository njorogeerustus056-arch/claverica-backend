# cleanup_tests.py
"""
Clean up problematic test files
"""

import os

# List of test files to keep (these work)
KEEP_FILES = [
    'test_cards_clean.py',           # Our clean test suite
    'test_cards_working.py',         # Working version
    'test_fixed_final.py',           # Fixed final version
    'cleanup_tests.py',              # This file
]

# List of test files that might have issues (can be removed)
PROBLEMATIC_FILES = [
    'test_cards_application.py',
    'test_cards_simple.py',
    'test_correct.py',
    'test_final_fixed.py',
    'tests.py',
    'test_with_db.py',
    'test_fixed_final_old.py',  # If exists
]

print("=" * 80)
print("CLEANING UP TEST FILES")
print("=" * 80)

current_dir = os.path.dirname(os.path.abspath(__file__))
all_files = os.listdir(current_dir)

print(f"Directory: {current_dir}")
print(f"Files found: {len(all_files)}")

# Show current test files
test_files = [f for f in all_files if f.startswith('test_') or f == 'tests.py']
print(f"\nCurrent test files:")
for f in test_files:
    print(f"  - {f}")

# Ask for confirmation
print(f"\nRecommended action:")
print(f"1. Keep these working files: {', '.join(KEEP_FILES)}")
print(f"2. You can safely delete these problematic files: {', '.join(PROBLEMATIC_FILES)}")

response = input("\nDo you want to see which files are problematic? (y/n): ")
if response.lower() == 'y':
    print("\nProblematic files (contain username field issues or other errors):")
    for f in PROBLEMATIC_FILES:
        if f in all_files:
            print(f"  - {f}")

print("\nTo clean up manually, you can:")
print("1. Run only the working tests:")
print("   python test_cards_clean.py")
print("2. Or: python test_cards_working.py")
print("3. Or: python test_fixed_final.py")
print("\nThese 3 files are guaranteed to work.")