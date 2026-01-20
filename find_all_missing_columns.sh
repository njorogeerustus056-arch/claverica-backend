#!/bin/bash
echo "🔍 SCANNING FOR ALL MISSING COLUMNS..."
echo "======================================"

# List of apps that might have issues
APPS="payments withdrawal transfers receipts tasks crypto escrow compliance kyc"

for app in $APPS; do
    echo ""
    echo "📦 Checking $app..."
    
    # Try to import models
    python -c "
try:
    import django
    django.setup()
    from django.apps import apps
    
    models = apps.get_app_config('$app').get_models()
    print(f'✅ $app: {len(models)} models found')
    
    # Try to count each model
    for model in models:
        try:
            count = model.objects.count()
            print(f'   - {model._meta.model_name}: {count} records')
        except Exception as e:
            print(f'   - {model._meta.model_name}: ❌ {str(e)[:100]}')
            
except Exception as e:
    print(f'❌ $app: {str(e)[:150]}')
"
done

echo ""
echo "======================================"
echo "🧪 QUICK TEST OF BROKEN ENDPOINTS..."
echo "Testing /admin/payments/card/ ..."
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8000/admin/payments/card/ || echo "Failed"
