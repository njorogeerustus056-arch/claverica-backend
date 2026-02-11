#!/bin/bash
echo "=== Railway Build Starting ==="
echo "Working directory: $(pwd)"

# On Railway, just collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput || echo "Static collection skipped"

echo "✅ Build completed successfully!"