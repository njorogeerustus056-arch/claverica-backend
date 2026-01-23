import http.client
import time

def test_endpoints():
    print("Testing Django endpoints...")
    
    endpoints = [
        "/",           # API root
        "/health/",    # Health check
        "/admin/",     # Admin login
        "/api/docs/",  # API documentation
    ]
    
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=10)
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting {endpoint}...")
            conn.request("GET", endpoint)
            response = conn.getresponse()
            print(f"  Status: {response.status} {response.reason}")
            print(f"  Headers: {dict(response.getheaders())}")
            
            # Read response body
            body = response.read().decode()[:200]
            if body:
                print(f"  Body: {body}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    conn.close()

if __name__ == "__main__":
    test_endpoints()