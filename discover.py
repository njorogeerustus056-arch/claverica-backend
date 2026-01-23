import requests
import json
import time

BASE_URL = "https://claverica-backend.onrender.com/api"

def test_endpoint(url, method="GET", data=None):
    """Test a single endpoint"""
    try:
        headers = {"Content-Type": "application/json"}
        
        if method == "GET":
            response = requests.get(url, timeout=10, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data or {}, timeout=10, headers=headers)
        elif method == "OPTIONS":
            response = requests.options(url, timeout=10, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data or {}, timeout=10, headers=headers)
        
        return {
            "url": url,
            "method": method,
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:500] if response.text else "",
            "time": response.elapsed.total_seconds()
        }
    except requests.exceptions.Timeout:
        return {"url": url, "method": method, "status": "TIMEOUT", "error": "Request timed out"}
    except Exception as e:
        return {"url": url, "method": method, "status": "ERROR", "error": str(e)}

def discover_api():
    print("🔍 API Endpoint Discovery")
    print("=" * 70)
    
    # Test the main endpoints we know
    endpoints_to_test = []
    
    # Test the working endpoint first
    print("\n1. Testing known working endpoint:")
    result = test_endpoint(f"{BASE_URL}/accounts/")
    print(f"   {result['method']} {result['url']} → {result['status']} ({result['time']:.2f}s)")
    print(f"   Response: {result['body'][:100]}...")
    
    # Test what methods are allowed on /api/accounts/
    print("\n2. Checking allowed methods on /api/accounts/:")
    result = test_endpoint(f"{BASE_URL}/accounts/", "OPTIONS")
    if 'allow' in result.get('headers', {}):
        print(f"   Allowed methods: {result['headers']['allow']}")
    
    # Try POST to /api/accounts/ - maybe this is how registration works
    print("\n3. Testing POST to /api/accounts/ (possible registration):")
    result = test_endpoint(
        f"{BASE_URL}/accounts/", 
        "POST", 
        {"email": f"test{int(time.time())}@example.com", "password": "test123"}
    )
    print(f"   POST {result['url']} → {result['status']}")
    print(f"   Response: {result['body'][:200]}")
    
    # Try PUT to /api/accounts/ - maybe this is login
    print("\n4. Testing PUT to /api/accounts/ (possible login):")
    result = test_endpoint(
        f"{BASE_URL}/accounts/", 
        "PUT", 
        {"email": "test@example.com", "password": "test123"}
    )
    print(f"   PUT {result['url']} → {result['status']}")
    print(f"   Response: {result['body'][:200]}")
    
    # Try different HTTP methods on /api/accounts/
    print("\n5. Testing all HTTP methods on /api/accounts/:")
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]:
        try:
            if method == "HEAD":
                response = requests.head(f"{BASE_URL}/accounts/", timeout=5)
                status = response.status_code
            else:
                result = test_endpoint(f"{BASE_URL}/accounts/", method)
                status = result['status']
            print(f"   {method:8} → {status}")
        except:
            print(f"   {method:8} → ERROR")
    
    # Check if there's versioning
    print("\n6. Checking for API versioning:")
    for version in ["v1", "v2", "v3", "v0", "v0.1", "v1.0"]:
        url = f"{BASE_URL}/{version}/accounts/"
        result = test_endpoint(url, "GET")
        if result['status'] != 404 and result['status'] != "ERROR":
            print(f"   Found: /{version}/accounts/ → {result['status']}")
    
    # Check common Django REST Framework patterns
    print("\n7. Checking Django REST Framework patterns:")
    drf_patterns = [
        "/accounts/register/",
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/user/",
        "/accounts/token/",
        "/accounts/token/refresh/",
        "/accounts/token/verify/",
        "/auth/login/",
        "/auth/register/",
        "/auth/token/login/",
        "/auth/token/logout/",
        "/auth/users/",
        "/auth/users/me/",
        "/auth/jwt/create/",
        "/auth/jwt/refresh/",
        "/auth/jwt/verify/",
    ]
    
    for pattern in drf_patterns:
        url = BASE_URL + pattern
        result = test_endpoint(url, "GET")
        if result['status'] not in [404, "ERROR", "TIMEOUT"]:
            print(f"   Found: {pattern} → {result['status']}")
            if result['status'] == 405:
                # Check what methods ARE allowed
                options_result = test_endpoint(url, "OPTIONS")
                if 'allow' in options_result.get('headers', {}):
                    print(f"     Allowed methods: {options_result['headers']['allow']}")

if __name__ == "__main__":
    discover_api()