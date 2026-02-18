"""
Test script to verify KYC Spec Dumpster setup is complete
"""
import os
import sys
from pathlib import Path

def test_kyc_spec_setup():
    """Test if all KYC Spec files and directories are properly created"""
    
    print("=" * 60)
    print(" KYC SPEC DUMPSTER SETUP TEST (NO DJANGO)")
    print("=" * 60)
    
    all_pass = True
    tests_passed = 0
    tests_failed = 0
    
    # Get project root
    BASE_DIR = Path(__file__).resolve().parent.parent
    print(f"Project root: {BASE_DIR}")
    
    # Define all required files and directories
    required_paths = {
        # ========== DIRECTORY STRUCTURE ==========
        '1. App directory': 'backend/kyc_spec/',
        '2. Storage directory': 'backend/kyc_spec/storage/',
        '3. Management commands': 'backend/kyc_spec/management/',
        '4. Commands subdirectory': 'backend/kyc_spec/management/commands/',
        '5. Tests directory': 'backend/kyc_spec/tests/',
        
        # ========== MEDIA STORAGE ==========
        '6. Media root': 'media/kyc_spec/',
        '7. Dumps directory': 'media/kyc_spec/dumps/',
        '8. Loan dumps': 'media/kyc_spec/dumps/loan/',
        '9. Insurance dumps': 'media/kyc_spec/dumps/insurance/',
        '10. Escrow dumps': 'media/kyc_spec/dumps/escrow/',
        '11. Logs directory': 'media/kyc_spec/logs/',
        '12. Uploads directory': 'media/kyc_spec/uploads/',
        
        # ========== CODE FILES ==========
        '13. App __init__.py': 'backend/kyc_spec/__init__.py',
        '14. Apps.py': 'backend/kyc_spec/apps.py',
        '15. Models.py': 'backend/kyc_spec/models.py',
        '16. Views.py': 'backend/kyc_spec/views.py',
        '17. Serializers.py': 'backend/kyc_spec/serializers.py',
        '18. Services.py': 'backend/kyc_spec/services.py',
        '19. Urls.py': 'backend/kyc_spec/urls.py',
        '20. Admin.py': 'backend/kyc_spec/admin.py',
        
        # ========== STORAGE FILES ==========
        '21. Storage __init__.py': 'backend/kyc_spec/storage/__init__.py',
        '22. Storage utils': 'backend/kyc_spec/storage_utils.py',
        
        # ========== MANAGEMENT COMMANDS ==========
        '23. Management __init__.py': 'backend/kyc_spec/management/__init__.py',
        '24. Commands __init__.py': 'backend/kyc_spec/management/commands/__init__.py',
        '25. Init storage command': 'backend/kyc_spec/management/commands/init_kyc_spec_storage.py',
        
        # ========== MEDIA FILES ==========
        '26. Leads CSV': 'media/kyc_spec/logs/leads.csv',
        '27. Submissions log': 'media/kyc_spec/logs/submissions.log',
        
        # ========== TEST FILES ==========
        '28. Tests __init__.py': 'backend/kyc_spec/tests/__init__.py',
    }
    
    # Test each path
    print("\n FILE STRUCTURE CHECK:")
    print("-" * 40)
    
    for test_name, rel_path in required_paths.items():
        full_path = os.path.join(BASE_DIR, rel_path)
        
        if os.path.exists(full_path):
            # Check if it's a directory or file
            if os.path.isdir(full_path):
                status = ""
                detail = "Directory exists"
            else:
                # Check if file has content
                if os.path.getsize(full_path) > 0:
                    status = ""
                    detail = f"File exists ({os.path.getsize(full_path)} bytes)"
                else:
                    status = ""
                    detail = "File exists but empty"
            tests_passed += 1
        else:
            status = ""
            detail = "MISSING!"
            tests_failed += 1
            all_pass = False
        
        print(f"{status} {test_name:40} {detail}")
    
    # Check file contents
    print("\n FILE CONTENT CHECK:")
    print("-" * 40)
    
    critical_files = {
        'Models.py': 'backend/kyc_spec/models.py',
        'Views.py': 'backend/kyc_spec/views.py',
        'Services.py': 'backend/kyc_spec/services.py',
        'Urls.py': 'backend/kyc_spec/urls.py',
        'Settings.py': 'backend/settings.py',
        'Main urls.py': 'backend/urls.py',
    }
    
    for file_name, rel_path in critical_files.items():
        full_path = os.path.join(BASE_DIR, rel_path)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            checks = []
            
            if file_name == 'Models.py':
                if 'KycSpecDump' in content:
                    checks.append(" Contains KycSpecDump model")
                else:
                    checks.append(" Missing KycSpecDump model")
                    
            elif file_name == 'Views.py':
                if 'KycSpecCollectView' in content:
                    checks.append(" Contains KycSpecCollectView")
                else:
                    checks.append(" Missing KycSpecCollectView")
                    
            elif file_name == 'Services.py':
                if 'create_dump' in content:
                    checks.append(" Contains create_dump method")
                else:
                    checks.append(" Missing create_dump method")
                    
            elif file_name == 'Urls.py' and 'kyc_spec' in rel_path:
                if 'collect/' in content:
                    checks.append(" Contains collect endpoint")
                else:
                    checks.append(" Missing collect endpoint")
                    
            elif file_name == 'Settings.py':
                if "'kyc_spec'" in content or '"kyc_spec"' in content:
                    checks.append(" kyc_spec in INSTALLED_APPS")
                else:
                    checks.append(" kyc_spec NOT in INSTALLED_APPS")
                    
            elif file_name == 'Main urls.py':
                if 'kyc-spec' in content.lower():
                    checks.append(" kyc-spec URLs included")
                else:
                    checks.append(" kyc-spec URLs missing")
            
            print(f" {file_name}:")
            for check in checks:
                print(f"   {check}")
        else:
            print(f" {file_name}: File not found")
            all_pass = False
    
    # Check for migrations
    print("\n MIGRATIONS CHECK:")
    print("-" * 40)
    
    migrations_dir = os.path.join(BASE_DIR, 'backend', 'kyc_spec', 'migrations')
    if os.path.exists(migrations_dir):
        migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py') and f != '__init__.py']
        if migration_files:
            print(f" Found {len(migration_files)} migration file(s):")
            for mig in sorted(migration_files):
                print(f"   - {mig}")
            tests_passed += 1
        else:
            print(" No migration files (run: python manage.py makemigrations kyc_spec)")
            tests_failed += 1
            all_pass = False
    else:
        print(" Migrations directory not found")
        tests_failed += 1
        all_pass = False
    
    # Check database
    print("\n DATABASE CHECK:")
    print("-" * 40)
    
    db_path = os.path.join(BASE_DIR, 'db.sqlite3')
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
        print(f" Database exists ({db_size:,} bytes)")
        tests_passed += 1
    else:
        print(" Database file not found")
        tests_failed += 1
        all_pass = False
    
    # Media directory check
    print("\n MEDIA DIRECTORY CHECK:")
    print("-" * 40)
    
    media_root = os.path.join(BASE_DIR, 'media', 'kyc_spec')
    if os.path.exists(media_root):
        print(f" Media directory exists: {media_root}")
        
        # List contents
        print("   Contents:")
        for root_dir, dirs, files in os.walk(media_root):
            level = root_dir.replace(media_root, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root_dir)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in sorted(files):
                if file != '.gitkeep':
                    file_path = os.path.join(root_dir, file)
                    size = os.path.getsize(file_path)
                    print(f"{subindent}{file} ({size} bytes)")
        tests_passed += 1
    else:
        print(" Media directory not found")
        tests_failed += 1
        all_pass = False
    
    # Summary
    print("\n" + "=" * 60)
    print(" TEST SUMMARY:")
    print("-" * 40)
    print(f"Total checks: {tests_passed + tests_failed}")
    print(f" Passed: {tests_passed}")
    print(f" Failed: {tests_failed}")
    
    if all_pass:
        print("\n SUCCESS! All KYC Spec files are properly created!")
        print("\nNext steps:")
        print("1. Run migrations:")
        print("   python manage.py makemigrations kyc_spec")
        print("   python manage.py migrate kyc_spec")
        print("\n2. Initialize storage:")
        print("   python manage.py init_kyc_spec_storage")
        print("\n3. Test endpoint:")
        print('   curl -X POST http://localhost:8000/api/kyc-spec/collect/ \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"product": "loan", "user_email": "test@example.com"}\'')
        print("\n4. Check admin:")
        print("   http://localhost:8000/admin/kyc_spec/kycspecdump/")
    else:
        print("\n Some tests failed. Missing files:")
        
        # Show missing files again
        for test_name, rel_path in required_paths.items():
            full_path = os.path.join(BASE_DIR, rel_path)
            if not os.path.exists(full_path):
                print(f"    {rel_path}")
        
        print("\nQuick fix commands:")
        print('''
# Create missing directories:
mkdir -p media/kyc_spec/dumps/loan
mkdir -p media/kyc_spec/dumps/insurance
mkdir -p media/kyc_spec/dumps/escrow
mkdir -p media/kyc_spec/logs
mkdir -p media/kyc_spec/uploads

# Create empty files:
echo "" > media/kyc_spec/logs/leads.csv
echo "[]" > media/kyc_spec/logs/submissions.log

# Create Python package files:
touch backend/kyc_spec/storage/__init__.py
touch backend/kyc_spec/management/__init__.py
touch backend/kyc_spec/management/commands/__init__.py
touch backend/kyc_spec/tests/__init__.py

# Create management command:
cat > backend/kyc_spec/management/commands/init_kyc_spec_storage.py << 'EOF'
from django.core.management.base import BaseCommand
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Initialize KYC Spec storage directories'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing KYC Spec storage...')
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        media_dir = base_dir / 'media' / 'kyc_spec'
        
        directories = [
            media_dir / 'dumps' / 'loan',
            media_dir / 'dumps' / 'insurance', 
            media_dir / 'dumps' / 'escrow',
            media_dir / 'logs',
            media_dir / 'uploads'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.stdout.write(f'  Created: {directory.relative_to(base_dir)}')
        
        (media_dir / 'logs' / 'leads.csv').touch()
        (media_dir / 'logs' / 'submissions.log').touch()
        
        self.stdout.write(self.style.SUCCESS(' KYC Spec storage initialized!'))
EOF
''')
    
    print("=" * 60)
    
    return all_pass

if __name__ == '__main__':
    success = test_kyc_spec_setup()
    sys.exit(0 if success else 1)