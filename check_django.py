echo import os > check_django.py
echo import django >> check_django.py
echo from django.apps import apps >> check_django.py
echo. >> check_django.py
echo os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings') >> check_django.py
echo. >> check_django.py
echo print("Testing Django app registry...") >> check_django.py
echo print("="*60) >> check_django.py
echo. >> check_django.py
echo try: >> check_django.py
echo     django.setup() >> check_django.py
echo     print("✅ Django setup successful") >> check_django.py
echo. >> check_django.py
echo     # Check what apps are registered >> check_django.py
echo     print("\\nRegistered apps with 'task' in name:") >> check_django.py
echo     for app_config in apps.get_app_configs(): >> check_django.py
echo         if 'task' in app_config.name: >> check_django.py
echo             print(f"  App: {app_config.name} (label: {app_config.label})") >> check_django.py
echo             # Check models >> check_django.py
echo             try: >> check_django.py
echo                 for model in app_config.get_models(): >> check_django.py
echo                     print(f"    Model: {model.__name__}") >> check_django.py
echo             except: >> check_django.py
echo                 print(f"    (Error getting models)") >> check_django.py
echo. >> check_django.py
echo except Exception as e: >> check_django.py
echo     print(f"❌ Django setup failed: {e}") >> check_django.py
echo     import traceback >> check_django.py
echo     traceback.print_exc() >> check_django.py