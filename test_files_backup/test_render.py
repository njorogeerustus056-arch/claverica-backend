# test_render.py
import requests
import time

print("Testing Render Endpoints...")
print("=" * 60)

endpoints = [
    ('/', 'Root'),
    ('/health/', 'Health Check'),
    ('/admin/', 'Admin'),
    ('/api/', 'API Root'),
    ('/api/auth/token/', 'JWT Token'),
]

render_url = "https://claverica-backend.onrender.com"

for endpoint, description in endpoints:
    try:
        full_url = render_url + endpoint
        print(f"\nTesting: {description} ({endpoint})")
        
        start = time.time()
        response = requests.get(full_url, timeout=30)
        elapsed = time.time() - start
        
        print(f"  Status: {response.status_code}")
        print(f"  Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            if 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    data = response.json()
                    print(f"  JSON Response: {data}")
                except:
                    print(f"  Response: {response.text[:200]}...")
            else:
                print(f"  HTML Response (length): {len(response.text)} chars")
        elif response.status_code == 404:
            print(f"  ❌ 404 Not Found - Endpoint doesn't exist")
        elif response.status_code == 500:
            print(f"  ❌ 500 Server Error")
            print(f"  Error: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout (service may be spinning up)")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("If /health/ returns 200: Service is running")
print("If /health/ returns user_model: Custom model is set")
print("If endpoints return 404: Code not deployed or URL config wrong")
print("=" * 60)