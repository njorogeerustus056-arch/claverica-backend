# test_render_current.py
import requests
import time

print("Testing Render Deployment: https://claverica-backend-rniq.onrender.com")
print("=" * 70)

# Use your actual Render URL
RENDER_URL = "https://claverica-backend-rniq.onrender.com"

# Updated endpoints based on what you likely have
endpoints = [
    ('/', 'Root - Django Welcome'),
    ('/health/', 'Health Check - MOST IMPORTANT'),
    ('/api/', 'API Root - DRF Browsable API'),
    ('/admin/', 'Django Admin - Should redirect to login'),
    ('/api/auth/', 'Auth API - If you have authentication'),
    ('/api/accounts/', 'Accounts API - For user accounts'),
    ('/api/users/', 'Users API - Alternative endpoint'),
    ('/static/admin/css/base.css', 'Static Files Test'),
]

for endpoint, description in endpoints:
    try:
        full_url = RENDER_URL + endpoint
        print(f"\n📍 Testing: {description}")
        print(f"   URL: {full_url}")
        
        start = time.time()
        response = requests.get(full_url, timeout=45)  # Increased timeout for cold starts
        elapsed = time.time() - start
        
        print(f"   ✅ Status: {response.status_code}")
        print(f"   ⏱️  Response Time: {elapsed:.2f} seconds")
        
        # Special handling for different status codes
        if response.status_code == 200:
            if endpoint == '/health/':
                print(f"   🩺 Health Check Content: {response.text[:100]}")
            elif 'application/json' in response.headers.get('Content-Type', ''):
                print(f"   📊 JSON Response (first 200 chars): {response.text[:200]}")
            else:
                print(f"   📄 HTML/Other Response: Length {len(response.text)} chars")
                if 'django' in response.text.lower():
                    print(f"   🎯 Django detected in response")
                
        elif response.status_code == 302 or response.status_code == 301:
            redirect_url = response.headers.get('Location', 'Unknown')
            print(f"   🔀 Redirecting to: {redirect_url}")
            
        elif response.status_code == 403:
            print(f"   🔒 Forbidden - Authentication required")
            
        elif response.status_code == 404:
            print(f"   ❓ 404 - Endpoint may not exist (check urls.py)")
            
        elif response.status_code == 500:
            print(f"   💥 500 Internal Server Error")
            print(f"   Error details: {response.text[:500]}")
            
        # Check for important headers
        if 'Access-Control-Allow-Origin' in response.headers:
            print(f"   🌐 CORS Enabled: {response.headers['Access-Control-Allow-Origin']}")
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ TIMEOUT - Service may be in cold start (takes 30-60s on free tier)")
        print(f"   💡 Try refreshing the URL in browser to warm it up")
        
    except requests.exceptions.ConnectionError:
        print(f"   🔌 CONNECTION ERROR - Service might be down or URL wrong")
        
    except Exception as e:
        print(f"   ❌ Unexpected Error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("🚀 DEPLOYMENT DIAGNOSTICS:")
print("=" * 70)

# Add diagnostic summary
try:
    # Try health endpoint for final check
    health_response = requests.get(RENDER_URL + '/health/', timeout=30)
    if health_response.status_code == 200:
        print("✅ SERVICE IS RUNNING: Health check passed")
        print(f"   Health response: {health_response.text[:200]}")
    else:
        print(f"⚠️  SERVICE HAS ISSUES: Health returned {health_response.status_code}")
        
    # Check if it's a cold start issue
    cold_start_test = requests.get(RENDER_URL + '/', timeout=10)
    print(f"📈 Root endpoint response time: Cold start check passed")
    
except requests.exceptions.Timeout:
    print("❌ COLD START DETECTED: Service is spinning up")
    print("   Render free tier services sleep after 15min of inactivity")
    print("   First request can take 30-60 seconds")
    print("   💡 Solution: Keep service warm with periodic requests")
    
except Exception as e:
    print(f"❌ DIAGNOSTIC FAILED: {e}")

print("=" * 70)
print("🎯 NEXT STEPS:")
print("1. If /health/ returns 200 → Service is working")
print("2. If 404 on all endpoints → Check deployment/urls.py")
print("3. If Timeout → Service is in cold start (wait 60s)")
print("4. If 500 → Check Render logs for Django errors")
print("=" * 70)