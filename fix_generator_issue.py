import django
from django.apps import apps
import inspect

print("🔧 Fixing generator/len() issue...")

# Patch get_models() to return list instead of generator
for app_config in apps.get_app_configs():
    original_get_models = app_config.get_models
    
    def patched_get_models(self, *args, **kwargs):
        result = original_get_models(*args, **kwargs)
        # Convert generator to list
        if inspect.isgenerator(result):
            return list(result)
        return result
    
    app_config.get_models = patched_get_models.__get__(app_config, type(app_config))

print("✅ Generator issue patched!")
