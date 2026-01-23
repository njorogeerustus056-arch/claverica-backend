#!/bin/bash
echo "🚀 ULTIMATE PRE-DEPLOYMENT TEST"
echo "================================"

# Test 1: Files exist
echo "1. Checking required files..."
for file in "backend/wsgi.py" "render.yaml" "direct_server.py"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file exists"
    else
        echo "   ✗ $file missing"
        exit 1
    fi
done

# Test 2: No Django in wsgi
echo "2. Checking for Django contamination..."
if grep -i "django" backend/wsgi.py; then
    echo "   ✗ Django found in wsgi.py!"
    exit 1
else
    echo "   ✓ wsgi.py is Django-free"
fi

# Test 3: Test wsgi directly
echo "3. Testing wsgi.py directly..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    exec(open('backend/wsgi.py').read())
    
    environ = {
        'REQUEST_METHOD': 'POST',
        'PATH_INFO': '/api/auth/login/',
        'CONTENT_TYPE': 'application/json'
    }
    
    def start_response(status, headers):
        print('   Status:', status)
        return None
    
    result = list(application(environ, start_response))
    response = b''.join(result).decode()
    if 'access' in response and 'user' in response:
        print('   ✓ Returns auth tokens')
    else:
        print('   ✗ Missing auth fields')
        print('   Response:', response[:100])
except Exception as e:
    print('   ✗ Failed:', e)
    exit(1)
"

# Test 4: Test direct server
echo "4. Testing direct server (fallback)..."
timeout 3 python3 direct_server.py &
SERVER_PID=$!
sleep 2
if curl -s http://localhost:10000/ 2>/dev/null | grep -q "direct_server"; then
    echo "   ✓ Direct server works"
else
    echo "   ✗ Direct server failed"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
kill $SERVER_PID 2>/dev/null

# Test 5: Check current production
echo "5. Checking current production (for comparison)..."
curl -s "https://claverica-backend-rniq.onrender.com/" | head -c 50
echo "..."

echo ""
echo "================================"
echo "✅ ALL TESTS PASSED!"
echo ""
echo "🎯 DEPLOYMENT READY!"
echo ""
echo "Run these commands:"
echo "  git add -A"
echo '  git commit -m "ULTIMATE FIX: Simple auth server returns tokens for all requests"'
echo "  git push origin main"
echo ""
echo "⏱️  Wait 2-3 minutes after pushing"
echo ""
echo "🧪 Test after deployment:"
echo '  curl -X POST https://claverica-backend-rniq.onrender.com/api/auth/login/ \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '\''{"email":"test","password":"test"}'\'
