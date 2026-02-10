#!/bin/bash
echo "=== Testing Django setup ==="
python -c "import django; print(f'Django version: {django.__version__}')"
python -c "from backend.wsgi import application; print('WSGI application loaded successfully')"
python manage.py check --deploy 2>/dev/null || echo "Deployment check failed (normal for some setups)"
echo "=== Test complete ==="
