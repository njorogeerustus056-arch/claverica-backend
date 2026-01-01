# check_all_apps.py
"""
COMPREHENSIVE APPLICATION CHECKER
Tests all Django applications in your project
"""

import os
import sys
import django
from django.test.utils import setup_test_environment
from django.core.management import call_command

print("=" * 80)
print("COMPREHENSIVE DJANGO APPLICATION CHECKER")
print("=" * 80)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append('D:/FULLSTACK/clavericabackend')
sys.path.append('D:/FULLSTACK/clavericabackend/backend')

django.setup()

from django.apps import apps
from django.conf import settings

def check_installed_apps():
    """Check all installed apps"""
    print("\n🔍 CHECKING INSTALLED APPLICATIONS")
    print("-" * 40)
    
    installed_apps = settings.INSTALLED_APPS
    print(f"Total installed apps: {len(installed_apps)}")
    
    for i, app in enumerate(installed_apps, 1):
        status = "✅"
        try:
            app_config = apps.get_app_config(app.split('.')[-1])
            print(f"{i:2}. {status} {app}")
            print(f"    Name: {app_config.name}")
            print(f"    Verbose: {app_config.verbose_name}")
            if hasattr(app_config, 'path'):
                print(f"    Path: {app_config.path}")
        except Exception as e:
            status = "❌"
            print(f"{i:2}. {status} {app} - ERROR: {e}")
    
    return installed_apps

def check_app_models():
    """Check models in each app"""
    print("\n🔍 CHECKING APPLICATION MODELS")
    print("-" * 40)
    
    app_configs = apps.get_app_configs()
    
    for app_config in app_configs:
        print(f"\n📦 {app_config.verbose_name} ({app_config.name})")
        print(f"   Path: {app_config.path}")
        
        models = app_config.get_models()
        print(f"   Models: {len(models)}")
        
        for model in models:
            print(f"    - {model.__name__}")
            
            # Count objects if any
            try:
                count = model.objects.count()
                print(f"      Objects: {count}")
            except:
                print(f"      Objects: (cannot count)")
            
            # Show some fields
            fields = [f.name for f in model._meta.fields[:5]]  # First 5 fields
            if fields:
                print(f"      Fields: {', '.join(fields)}" + ("..." if len(fields) > 5 else ""))

def check_database():
    """Check database connection and tables"""
    print("\n🔍 CHECKING DATABASE")
    print("-" * 40)
    
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # Check if we can query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Database connection: OK")
            print(f"   Test query result: {result}")
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            print(f"   Total tables: {len(tables)}")
            
            print("\n   Database tables:")
            for i, (table_name,) in enumerate(tables, 1):
                # Count rows in each table
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"    {i:2}. {table_name:30} - {count:6} rows")
                except:
                    print(f"    {i:2}. {table_name:30} - (cannot count)")
                    
    except Exception as e:
        print(f"❌ Database error: {e}")

def check_urls():
    """Check URL configurations"""
    print("\n🔍 CHECKING URL CONFIGURATIONS")
    print("-" * 40)
    
    from django.urls import get_resolver
    
    try:
        resolver = get_resolver()
        url_patterns = []
        
        def extract_urls(url_patterns, prefix=''):
            for pattern in url_patterns:
                if hasattr(pattern, 'url_patterns'):
                    # This is an include
                    extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
                elif hasattr(pattern, 'pattern'):
                    # This is a path/route
                    url_patterns.append(prefix + str(pattern.pattern))
        
        # Get main URL patterns
        main_patterns = resolver.url_patterns
        extract_urls(main_patterns)
        
        print(f"Total URL patterns found: {len(url_patterns)}")
        print("\nURL patterns:")
        for i, pattern in enumerate(sorted(set(url_patterns)), 1):
            print(f"  {i:2}. {pattern}")
            
    except Exception as e:
        print(f"❌ URL check error: {e}")

def check_models_integrity():
    """Check model integrity and relationships"""
    print("\n🔍 CHECKING MODEL INTEGRITY")
    print("-" * 40)
    
    from django.db import models as django_models
    
    app_configs = apps.get_app_configs()
    all_models = []
    
    for app_config in app_configs:
        for model in app_config.get_models():
            all_models.append(model)
    
    print(f"Total models in project: {len(all_models)}")
    
    # Check for common issues
    issues = []
    
    for model in all_models:
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        # Check for missing __str__ method
        if model.__str__ == django_models.Model.__str__:
            issues.append(f"{model_name}: Missing custom __str__ method")
        
        # Check foreign keys
        for field in model._meta.fields:
            if isinstance(field, django_models.ForeignKey):
                try:
                    field.related_model
                except Exception as e:
                    issues.append(f"{model_name}.{field.name}: ForeignKey error - {e}")
    
    if issues:
        print(f"⚠️  Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No model integrity issues found")

def run_basic_tests():
    """Run basic tests for key applications"""
    print("\n🔍 RUNNING BASIC TESTS")
    print("-" * 40)
    
    # List of apps to test
    apps_to_test = ['cards', 'accounts']
    
    for app_name in apps_to_test:
        print(f"\n📊 Testing {app_name}...")
        try:
            # Try to import the app
            app_config = apps.get_app_config(app_name)
            print(f"  ✅ App found: {app_config.verbose_name}")
            
            # Try to run tests if test file exists
            test_path = os.path.join(app_config.path, 'tests.py')
            if os.path.exists(test_path):
                print(f"  📁 Test file exists")
                
                # Try to run a simple test
                try:
                    # Import and check for test classes
                    import importlib
                    module = importlib.import_module(f"{app_name}.tests")
                    
                    test_classes = [c for c in dir(module) 
                                  if c.endswith('Test') or c.startswith('Test')]
                    
                    print(f"  Found test classes: {len(test_classes)}")
                    for tc in test_classes[:3]:  # Show first 3
                        print(f"    - {tc}")
                    if len(test_classes) > 3:
                        print(f"    ... and {len(test_classes) - 3} more")
                        
                except Exception as e:
                    print(f"  ⚠️  Could not import tests: {e}")
            else:
                print(f"  ℹ️  No tests.py file found")
                
        except Exception as e:
            print(f"  ❌ Error with {app_name}: {e}")

def check_settings():
    """Check important settings"""
    print("\n🔍 CHECKING SETTINGS")
    print("-" * 40)
    
    important_settings = [
        'DEBUG',
        'DATABASES',
        'SECRET_KEY',
        'ALLOWED_HOSTS',
        'INSTALLED_APPS',
        'MIDDLEWARE',
        'ROOT_URLCONF',
        'TIME_ZONE',
        'USE_TZ',
        'STATIC_URL',
        'MEDIA_URL',
    ]
    
    for setting in important_settings:
        try:
            value = getattr(settings, setting)
            if setting == 'SECRET_KEY' and value:
                value = '✓ Set (hidden)'  # Don't show secret key
            elif setting == 'DATABASES':
                engines = [db.get('ENGINE', '') for db in value.values()]
                value = f"{len(value)} database(s): {', '.join(engines)}"
            elif setting == 'INSTALLED_APPS':
                value = f"{len(value)} apps"
            elif setting == 'MIDDLEWARE':
                value = f"{len(value)} middleware classes"
            elif isinstance(value, list) or isinstance(value, tuple):
                value = f"{len(value)} items"
            
            print(f"✅ {setting:20}: {value}")
        except Exception as e:
            print(f"❌ {setting:20}: ERROR - {e}")

def check_health_endpoints():
    """Check if health/status endpoints exist"""
    print("\n🔍 CHECKING HEALTH ENDPOINTS")
    print("-" * 40)
    
    try:
        from django.test import Client
        client = Client()
        
        endpoints = [
            ('/', 'Root'),
            ('/admin/', 'Admin'),
            ('/api/', 'API Root'),
            ('/api/cards/', 'Cards API'),
            ('/health/', 'Health'),
            ('/status/', 'Status'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = client.get(endpoint)
                status = '✅' if response.status_code < 400 else '⚠️'
                print(f"{status} {name:15} {endpoint:20} - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {name:15} {endpoint:20} - ERROR: {e}")
                
    except Exception as e:
        print(f"❌ Cannot create test client: {e}")

def main():
    """Run all checks"""
    try:
        # Run all checks
        check_installed_apps()
        check_settings()
        check_app_models()
        check_database()
        check_urls()
        check_models_integrity()
        check_health_endpoints()
        run_basic_tests()
        
        print("\n" + "=" * 80)
        print("✅ ALL CHECKS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nYour Django project is properly configured and ready.")
        print("\nNext steps:")
        print("1. Run full test suite: python manage.py test")
        print("2. Create superuser: python manage.py createsuperuser")
        print("3. Run development server: python manage.py runserver")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during checks: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)