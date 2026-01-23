import os
import sys
import subprocess
import time

# Use test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

try:
    import django
    django.setup()
    print("✅ Django setup successful with test settings")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("\nTrying to install missing packages...")
    
    # Try to install health_check
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "django-health-check"])
        print("Installed django-health-check, retrying...")
        
        # Retry Django setup
        django.setup()
        print("✅ Django setup successful after installing packages")
    except Exception as e2:
        print(f"❌ Still failed: {e2}")
        print("\nCreating minimal test environment...")
        # Continue with minimal setup
        pass

# List of apps to test
all_possible_apps = [
    'accounts', 'cards', 'compliance', 'crypto', 'escrow',
    'notifications', 'payments', 'receipts', 'tasks',
    'transactions', 'transfers'
]

print(f"\n🔍 Checking for apps in: {os.getcwd()}")
existing_apps = []

for app in all_possible_apps:
    app_path = os.path.join(os.getcwd(), app)
    if os.path.exists(app_path) and os.path.isdir(app_path):
        # Check if it's a Django app
        has_models = os.path.exists(os.path.join(app_path, 'models.py'))
        has_apps = os.path.exists(os.path.join(app_path, 'apps.py'))
        
        if has_models or has_apps:
            existing_apps.append(app)
            status = "✅" if has_models else "⚠️ "
            print(f"{status} Found: {app}" + (" (no models.py)" if not has_models else ""))
        else:
            print(f"❌ Not a Django app: {app}")
    else:
        print(f"❌ Missing: {app}")

print(f"\n🎯 Found {len(existing_apps)} apps: {', '.join(existing_apps)}")

def run_tests_for_app(app_name):
    """Run tests for a single app"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {app_name}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        # Use test settings
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'test_settings'
        
        # Run Django test command
        result = subprocess.run(
            [sys.executable, 'manage.py', 'test', app_name, '--verbosity=1'],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout per app
            env=env
        )
        
        elapsed = time.time() - start_time
        
        # Check results
        if result.returncode == 0:
            print(f"✅ {app_name} - PASSED ({elapsed:.1f}s)")
            # Show test count if available
            for line in result.stdout.split('\n'):
                line_lower = line.lower()
                if ('test' in line_lower and 
                    ('ok' in line_lower or 'failed' in line_lower or 'error' in line_lower) and
                    'ran' in line_lower):
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ {app_name} - FAILED ({elapsed:.1f}s)")
            print(f"   Exit code: {result.returncode}")
            
            # Show relevant error output
            lines = result.stderr.split('\n') + result.stdout.split('\n')
            error_lines = []
            for line in lines:
                line_lower = line.lower()
                if ('error' in line_lower or 
                    'fail' in line_lower or 
                    'traceback' in line_lower or
                    'import' in line_lower or
                    'module' in line_lower):
                    error_lines.append(line.strip())
            
            if error_lines:
                print("\n   Relevant errors (first 5):")
                for err in error_lines[:5]:
                    print(f"   - {err}")
            
            # Show full traceback if it exists
            if 'Traceback' in result.stderr:
                print("\n   Traceback:")
                traceback_lines = result.stderr.split('\n')
                in_traceback = False
                for line in traceback_lines[-10:]:  # Last 10 lines of traceback
                    if 'Traceback' in line:
                        in_traceback = True
                    if in_traceback and line.strip():
                        print(f"   {line}")
            
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {app_name} - TIMEOUT after 2 minutes")
        return False
    except Exception as e:
        print(f"💥 {app_name} - ERROR: {str(e)}")
        import traceback
        print(f"   {traceback.format_exc()}")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("🚀 STARTING COMPREHENSIVE APP TESTS")
    print("="*60)
    
    # Check if we can run manage.py
    if not os.path.exists('manage.py'):
        print("❌ ERROR: manage.py not found!")
        print("Current directory:", os.getcwd())
        return
    
    print(f"Using manage.py from: {os.path.abspath('manage.py')}")
    print(f"Using settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    
    # Run tests for each existing app
    results = {}
    for app in existing_apps:
        results[app] = run_tests_for_app(app)
        time.sleep(1)  # Brief pause between apps
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for app, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {app}")
    
    print(f"\nTotal: {passed}/{total} apps passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! You can now safely restructure.")
        print("\nNext steps:")
        print("1. Backup database: python manage.py dumpdata > backup.json")
        print("2. Move apps to backend/ directory")
        print("3. Update settings.py")
        print("4. Run tests again to verify")
    else:
        print(f"\n⚠️  {total-passed} app(s) failed. Fix tests before restructuring.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)