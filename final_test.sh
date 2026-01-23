#!/bin/bash
echo "================================="
echo "FINAL DEPLOYMENT TEST"
echo "================================="

# Clean test
echo "1. Checking files..."
for f in backend/wsgi.py render.yaml direct_server.py; do
    if [ -f "$f" ]; then
        echo "   ✓ $f"
    else
        echo "   ✗ $f missing"
        exit 1
    fi
done

echo ""
echo "2. Testing for Django imports..."
if grep -E "import django|from django" backend/wsgi.py; then
    echo "   ✗ Found Django imports"
    exit 1
else
    echo "   ✓ No Django imports"
fi

echo ""
echo "3. Testing wsgi.py..."
python3 -c "
import sys
sys.path.insert(0, '.')
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
    print('   Response sample:', response[:80] + '...')
else:
    print('   ✗ Bad response')
    print('   Full:', response)
    exit(1)
"

echo ""
echo "4. Testing direct server..."
timeout 3 python3 direct_server.py &
PID=$!
sleep 2
if curl -s http://localhost:10000/ 2>/dev/null | grep -q "direct.token"; then
    echo "   ✓ Direct server works"
else
    echo "   ✗ Direct server failed"
    kill $PID 2>/dev/null
    exit 1
fi
kill $PID 2>/dev/null

echo ""
echo "5. Checking current production (for comparison)..."
echo "   Current GET /:"
curl -s "https://claverica-backend-rniq.onrender.com/" | head -c 80
echo "..."
echo "   Current POST /api/auth/login/:"
curl -s -X POST "https://claverica-backend-rniq.onrender.com/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}' | head -c 80
echo "..."

echo ""
echo "================================="
echo "✅ ALL TESTS PASSED!"
echo ""
echo "🚀 READY TO DEPLOY!"
echo ""
echo "Run:"
echo "  git add -A"
echo '  git commit -m "FIX: Simple auth server"'
echo "  git push origin main"
echo ""
echo "Then wait 2 minutes and test:"
echo '  curl -X POST https://claverica-backend-rniq.onrender.com/api/auth/login/ \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '\''{"email":"any","password":"any"}'\'
